"""End-to-end baseline and patent-inspired optimized clustering."""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score

from .dtw import dtw_reassign
from .features import KPCALocalityFusion
from .preprocessing import LoadPreprocessor


@dataclass
class ClusteringResult:
    labels: np.ndarray
    n_clusters: int
    silhouette: float
    inertia_by_k: dict[int, float]
    repaired_values: int
    n_components: int


class OptimizedLoadClusterer:
    def __init__(self, k_range: range = range(2, 7), random_state: int = 42):
        self.k_range = k_range
        self.random_state = random_state

    def _select_k(self, x: np.ndarray) -> tuple[int, dict[int, float]]:
        inertias, silhouettes = {}, {}
        for k in self.k_range:
            model = KMeans(k, n_init=20, random_state=self.random_state).fit(x)
            inertias[k] = float(model.inertia_)
            silhouettes[k] = float(silhouette_score(x, model.labels_))
        # Kneedle geometry: maximum perpendicular distance from the normalized
        # WCSS curve to the line connecting its endpoints.
        ks = np.asarray(list(inertias), dtype=float)
        ys = np.asarray(list(inertias.values()), dtype=float)
        x_norm = (ks - ks.min()) / max(np.ptp(ks), 1e-12)
        y_norm = (ys - ys.min()) / max(np.ptp(ys), 1e-12)
        p1, p2 = np.array([x_norm[0], y_norm[0]]), np.array([x_norm[-1], y_norm[-1]])
        line = p2 - p1
        distances = np.abs(np.cross(line, np.c_[x_norm, y_norm] - p1)) / max(np.linalg.norm(line), 1e-12)
        elbow_indices = np.flatnonzero(np.isclose(distances, distances.max(), rtol=0.05))
        # Silhouette is only a tie-breaker among geometrically equivalent elbows.
        elbow_ks = [int(ks[i]) for i in elbow_indices]
        return max(elbow_ks, key=lambda k: silhouettes[k]), inertias

    def fit_predict(self, curves: np.ndarray, context: np.ndarray | None = None) -> ClusteringResult:
        prep = LoadPreprocessor()
        clean_curves = prep.fit_transform(curves)
        x = clean_curves if context is None else np.hstack([clean_curves, MinMaxContext().fit_transform(context)])
        fusion = KPCALocalityFusion()
        embedded = fusion.fit_transform(x)
        k, inertias = self._select_k(embedded)
        initial = KMeans(k, n_init=30, random_state=self.random_state).fit_predict(embedded)
        refined = dtw_reassign(clean_curves, initial, k)
        # Patent step 6: second clustering after DTW-based reallocation.
        centers = np.vstack([embedded[refined == c].mean(axis=0) for c in range(k)])
        final = KMeans(k, init=centers, n_init=1, random_state=self.random_state).fit_predict(embedded)
        return ClusteringResult(
            labels=final,
            n_clusters=k,
            silhouette=float(silhouette_score(embedded, final)),
            inertia_by_k=inertias,
            repaired_values=prep.repaired_count_,
            n_components=fusion.n_components_,
        )


class MinMaxContext:
    def fit_transform(self, x: np.ndarray) -> np.ndarray:
        x = np.asarray(x, float)
        low, high = np.nanmin(x, axis=0), np.nanmax(x, axis=0)
        return (np.nan_to_num(x, nan=np.nanmedian(x, axis=0)) - low) / np.where(high - low < 1e-9, 1, high - low)


def evaluate(true_labels: np.ndarray, predicted: np.ndarray) -> float:
    """Adjusted Rand Index is permutation-invariant and valid for clustering."""
    return float(adjusted_rand_score(true_labels, predicted))
