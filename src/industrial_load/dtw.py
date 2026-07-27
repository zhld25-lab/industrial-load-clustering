"""Dynamic Time Warping distance and cluster reassignment."""

from __future__ import annotations

import numpy as np


def dtw_distance(a: np.ndarray, b: np.ndarray, window: int | None = None) -> float:
    a, b = np.asarray(a, float), np.asarray(b, float)
    window = max(window or max(len(a), len(b)), abs(len(a) - len(b)))
    cost = np.full((len(a) + 1, len(b) + 1), np.inf)
    cost[0, 0] = 0.0
    for i in range(1, len(a) + 1):
        for j in range(max(1, i - window), min(len(b), i + window) + 1):
            cost[i, j] = abs(a[i - 1] - b[j - 1]) + min(
                cost[i - 1, j], cost[i, j - 1], cost[i - 1, j - 1]
            )
    return float(cost[-1, -1])


def dtw_reassign(curves: np.ndarray, labels: np.ndarray, n_clusters: int, window: int = 4) -> np.ndarray:
    medoids = []
    for cluster in range(n_clusters):
        members = curves[labels == cluster]
        if len(members) == 0:
            medoids.append(curves[0])
            continue
        pair_cost = np.array([
            sum(dtw_distance(a, b, window) for b in members) for a in members
        ])
        medoids.append(members[int(pair_cost.argmin())])
    return np.asarray([
        int(np.argmin([dtw_distance(curve, medoid, window) for medoid in medoids]))
        for curve in curves
    ])

