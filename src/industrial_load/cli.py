"""Command-line reproducible experiment."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import numpy as np
from sklearn.cluster import KMeans
from sklearn.impute import KNNImputer
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.preprocessing import MinMaxScaler

from .data import generate_park_data
from .pipeline import OptimizedLoadClusterer


def run(seed: int = 42, output: str = "results") -> dict[str, float | int]:
    frame, truth = generate_park_data(seed=seed)
    load_cols = [c for c in frame if c.startswith("load_h")]
    context_cols = ["temperature_c", "tariff_usd_kwh", "renewable_policy_index", "equipment_efficiency"]
    curves = frame[load_cols].to_numpy()
    context = frame[context_cols].to_numpy()

    baseline_x = MinMaxScaler().fit_transform(KNNImputer(n_neighbors=5).fit_transform(curves))
    baseline_labels = KMeans(3, n_init=20, random_state=seed).fit_predict(baseline_x)
    model = OptimizedLoadClusterer(random_state=seed)
    result = model.fit_predict(curves, context)
    metrics = {
        "seed": seed,
        "samples": len(frame),
        "selected_clusters": result.n_clusters,
        "repaired_values": result.repaired_values,
        "kpca_components": result.n_components,
        "baseline_ari": float(adjusted_rand_score(truth, baseline_labels)),
        "optimized_ari": float(adjusted_rand_score(truth, result.labels)),
        "baseline_silhouette": float(silhouette_score(baseline_x, baseline_labels)),
        "optimized_silhouette": result.silhouette,
    }
    metrics["ari_relative_change_pct"] = (
        100 * (metrics["optimized_ari"] - metrics["baseline_ari"]) / max(abs(metrics["baseline_ari"]), 1e-9)
    )
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    frame.assign(true_pattern=truth, predicted_cluster=result.labels).to_csv(out / "clustered_loads.csv", index=False)
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", default="results")
    args = parser.parse_args()
    print(json.dumps(run(args.seed, args.output), indent=2))


if __name__ == "__main__":
    main()

