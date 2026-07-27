"""KPCA plus graph-Laplacian local-structure feature fusion."""

from __future__ import annotations

import numpy as np
from scipy.linalg import eigh
from sklearn.decomposition import KernelPCA
from sklearn.neighbors import kneighbors_graph


class KPCALocalityFusion:
    """Engineering interpretation of the patent's KPCA-KLPP fusion.

    KPCA retains nonlinear global variance. A heat-kernel k-NN graph then
    supplies the local Laplacian embedding. Both standardized views are fused.
    """

    def __init__(
        self,
        variance_threshold: float = 0.85,
        n_neighbors: int = 7,
        gamma: float | None = None,
        local_weight: float = 0.35,
        max_components: int = 12,
    ):
        self.variance_threshold = variance_threshold
        self.n_neighbors = n_neighbors
        self.gamma = gamma
        self.local_weight = local_weight
        self.max_components = max_components

    @staticmethod
    def _zscore(x: np.ndarray) -> np.ndarray:
        return (x - x.mean(axis=0)) / np.where(x.std(axis=0) < 1e-9, 1.0, x.std(axis=0))

    def fit_transform(self, x: np.ndarray) -> np.ndarray:
        n_max = min(self.max_components, x.shape[0] - 1, x.shape[1])
        gamma = self.gamma or 1.0 / x.shape[1]
        kpca = KernelPCA(n_components=n_max, kernel="rbf", gamma=gamma, eigen_solver="arpack")
        global_z = kpca.fit_transform(x)
        eigenvalues = np.maximum(np.asarray(kpca.eigenvalues_), 0)
        cumulative = np.cumsum(eigenvalues) / max(eigenvalues.sum(), 1e-12)
        self.n_components_ = max(2, int(np.searchsorted(cumulative, self.variance_threshold) + 1))
        global_z = global_z[:, : self.n_components_]

        graph = kneighbors_graph(
            x, n_neighbors=min(self.n_neighbors, x.shape[0] - 1),
            mode="distance", include_self=False,
        ).toarray()
        nonzero = graph[graph > 0]
        scale = float(np.median(nonzero) ** 2) if nonzero.size else 1.0
        weights = np.where(graph > 0, np.exp(-(graph**2) / max(scale, 1e-12)), 0.0)
        weights = np.maximum(weights, weights.T)
        degree = np.diag(weights.sum(axis=1))
        laplacian = degree - weights
        vals, vecs = eigh(laplacian, degree + np.eye(x.shape[0]) * 1e-8)
        local_z = vecs[:, 1 : self.n_components_ + 1]
        return np.hstack([
            self._zscore(global_z) * (1.0 - self.local_weight),
            self._zscore(local_z) * self.local_weight,
        ])

