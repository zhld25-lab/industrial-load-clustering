"""Synthetic, labeled load profiles for reproducible evaluation."""

from __future__ import annotations

import numpy as np
import pandas as pd


LABELS = ("energy_intensive", "distributed_energy", "ev_charging")


def _daily_profile(kind: str, hours: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    if kind == "energy_intensive":
        work = ((hours >= 7) & (hours <= 19)).astype(float)
        profile = 0.35 + 0.62 * work + 0.12 * np.exp(-0.5 * ((hours - 14) / 2.2) ** 2)
    elif kind == "distributed_energy":
        demand = 0.50 + 0.17 * np.exp(-0.5 * ((hours - 19) / 2.5) ** 2)
        solar = 0.58 * np.exp(-0.5 * ((hours - 13) / 2.8) ** 2)
        profile = demand - solar
    elif kind == "ev_charging":
        morning = 0.34 * np.exp(-0.5 * ((hours - 8) / 1.5) ** 2)
        evening = 0.70 * np.exp(-0.5 * ((hours - 20) / 2.3) ** 2)
        profile = 0.20 + morning + evening
    else:
        raise ValueError(f"Unknown profile type: {kind}")
    return profile + rng.normal(0, 0.035, hours.size)


def generate_park_data(
    n_per_class: int = 30,
    periods: int = 24,
    seed: int = 42,
    anomaly_rate: float = 0.025,
    missing_rate: float = 0.02,
) -> tuple[pd.DataFrame, np.ndarray]:
    """Generate load profiles plus weather, tariff, and renewable-policy features.

    Labels are returned only for evaluation and are never passed to the clustering model.
    """
    rng = np.random.default_rng(seed)
    hours = np.arange(periods) % 24
    rows: list[dict[str, float | str]] = []
    labels: list[str] = []
    for kind in LABELS:
        for i in range(n_per_class):
            # Facilities often start nominally identical shifts at different
            # clock times; this is the failure mode DTW is intended to handle.
            phase = int(rng.integers(-3, 4))
            scale = rng.uniform(750, 1450)
            curve = np.roll(_daily_profile(kind, hours, rng), phase) * scale
            temperature = rng.normal(24, 6)
            tariff = rng.uniform(0.08, 0.19)
            policy_index = rng.uniform(0.65, 1.0) if kind == "distributed_energy" else rng.uniform(0.1, 0.7)
            row: dict[str, float | str] = {
                "entity_id": f"{kind[:3]}-{i:03d}",
                "temperature_c": temperature,
                "tariff_usd_kwh": tariff,
                "renewable_policy_index": policy_index,
                "equipment_efficiency": rng.uniform(0.78, 0.97),
            }
            row.update({f"load_h{h:02d}_kw": float(curve[h]) for h in range(periods)})
            rows.append(row)
            labels.append(kind)

    frame = pd.DataFrame(rows)
    load_cols = [c for c in frame if c.startswith("load_h")]
    # Pandas 3 may expose a read-only array; anomaly injection requires an
    # explicit writable copy.
    values = frame[load_cols].to_numpy(copy=True)
    corrupt = rng.random(values.shape) < anomaly_rate
    values[corrupt] *= rng.choice([0.05, 3.5], size=corrupt.sum())
    missing = rng.random(values.shape) < missing_rate
    values[missing] = np.nan
    frame.loc[:, load_cols] = values
    return frame, np.asarray(labels)
