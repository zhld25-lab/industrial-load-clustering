"""Patent-aligned anomaly detection, KNN repair, and min-max scaling."""

from __future__ import annotations

import numpy as np
from sklearn.impute import KNNImputer
from sklearn.preprocessing import MinMaxScaler


class LoadPreprocessor:
    def __init__(self, n_neighbors: int = 5, outlier_z: float = 3.5):
        self.n_neighbors = n_neighbors
        self.outlier_z = outlier_z
        self.imputer = KNNImputer(n_neighbors=n_neighbors, weights="distance")
        self.scaler = MinMaxScaler()
        self.repaired_count_ = 0

    def fit_transform(self, x: np.ndarray) -> np.ndarray:
        x = np.asarray(x, dtype=float).copy()
        median = np.nanmedian(x, axis=0)
        mad = np.nanmedian(np.abs(x - median), axis=0)
        robust_z = 0.6745 * (x - median) / np.where(mad < 1e-9, 1.0, mad)
        bad = np.abs(robust_z) > self.outlier_z
        x[bad] = np.nan
        self.repaired_count_ = int(np.isnan(x).sum())
        repaired = self.imputer.fit_transform(x)
        return self.scaler.fit_transform(repaired)

