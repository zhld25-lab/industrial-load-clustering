"""Synthetic time-series generation and SQLite persistence for the demo."""

from __future__ import annotations

import sqlite3
import argparse
from pathlib import Path

import numpy as np
import pandas as pd


DATA_NOTICE = (
    "SYNTHETIC DATA ONLY. The original industrial project was private and its "
    "operational data cannot be disclosed. Values in this repository were "
    "generated for demonstration and do not represent any real facility."
)

FACILITY_TYPES = (
    ("energy_intensive", "Metal processing", 1650.0, 0.10),
    ("distributed_energy", "Electronics manufacturing", 1250.0, 0.55),
    ("ev_charging", "Logistics and charging", 1050.0, 0.20),
)


def generate_hourly_dataset(
    days: int = 30,
    facilities_per_type: int = 4,
    seed: int = 42,
    start: str = "2026-01-01",
) -> pd.DataFrame:
    """Create a realistic but fully synthetic, labeled hourly load dataset."""
    if days < 1 or facilities_per_type < 1:
        raise ValueError("days and facilities_per_type must be positive")

    rng = np.random.default_rng(seed)
    timestamps = pd.date_range(start, periods=days * 24, freq="h", tz="America/New_York")
    rows: list[dict[str, object]] = []

    for type_index, (kind, segment, capacity, renewable_ratio) in enumerate(FACILITY_TYPES):
        for facility_index in range(facilities_per_type):
            facility_id = f"F-{type_index + 1}{facility_index + 1:02d}"
            scale = rng.uniform(0.82, 1.12)
            efficiency = rng.uniform(0.80, 0.96)
            phase = int(rng.integers(-1, 2))

            for timestamp in timestamps:
                hour = (timestamp.hour + phase) % 24
                weekend = timestamp.dayofweek >= 5
                seasonal = 1 + 0.04 * np.sin(2 * np.pi * (timestamp.dayofyear - 15) / 365)
                temperature = (
                    7
                    + 7 * np.sin(2 * np.pi * (timestamp.hour - 8) / 24)
                    + 2 * np.sin(2 * np.pi * timestamp.dayofyear / 10)
                    + rng.normal(0, 1.2)
                )
                solar_shape = max(0.0, np.sin(np.pi * (timestamp.hour - 6) / 12))

                if kind == "energy_intensive":
                    base = 0.42 + (0.47 if 7 <= hour <= 19 else 0.08)
                    base *= 0.78 if weekend else 1.0
                elif kind == "distributed_energy":
                    production = 0.48 + (0.28 if 8 <= hour <= 18 else 0.04)
                    base = production * (0.72 if weekend else 1.0)
                else:
                    morning = 0.24 * np.exp(-0.5 * ((hour - 8) / 1.7) ** 2)
                    evening = 0.62 * np.exp(-0.5 * ((hour - 20) / 2.4) ** 2)
                    base = 0.18 + morning + evening + (0.10 if weekend else 0.0)

                gross_load = max(20.0, capacity * scale * seasonal * base + rng.normal(0, capacity * 0.025))
                renewable = max(
                    0.0,
                    capacity * renewable_ratio * solar_shape * rng.uniform(0.82, 1.08),
                )
                net_load = max(0.0, gross_load - renewable)
                peak_period = timestamp.dayofweek < 5 and 16 <= timestamp.hour <= 21
                tariff = 0.091 + (0.074 if peak_period else 0.018 if 8 <= timestamp.hour <= 15 else 0.0)

                random_value = rng.random()
                quality_flag = "valid"
                is_anomaly = 0
                if random_value < 0.006:
                    net_load *= rng.choice([0.18, 2.25])
                    gross_load = net_load + renewable
                    quality_flag = "anomaly"
                    is_anomaly = 1
                elif random_value < 0.011:
                    gross_load = np.nan
                    net_load = np.nan
                    quality_flag = "missing"

                rows.append(
                    {
                        "timestamp": timestamp.isoformat(),
                        "park_id": "PARK-DEMO-01",
                        "facility_id": facility_id,
                        "facility_type": kind,
                        "industry_segment": segment,
                        "contracted_capacity_kw": round(capacity * scale, 2),
                        "equipment_efficiency": round(efficiency, 4),
                        "gross_load_kw": round(gross_load, 3) if pd.notna(gross_load) else np.nan,
                        "renewable_generation_kw": round(renewable, 3),
                        "net_load_kw": round(net_load, 3) if pd.notna(net_load) else np.nan,
                        "temperature_c": round(temperature, 2),
                        "tariff_usd_kwh": round(tariff, 4),
                        "is_weekend": int(weekend),
                        "is_anomaly": is_anomaly,
                        "quality_flag": quality_flag,
                        "data_source": "synthetic_generator_v1",
                    }
                )

    return pd.DataFrame(rows)


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS dataset_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS parks (
    park_id TEXT PRIMARY KEY,
    park_name TEXT NOT NULL,
    region TEXT NOT NULL,
    timezone TEXT NOT NULL,
    data_classification TEXT NOT NULL CHECK (data_classification = 'synthetic')
);

CREATE TABLE IF NOT EXISTS facilities (
    facility_id TEXT PRIMARY KEY,
    park_id TEXT NOT NULL REFERENCES parks(park_id),
    facility_type TEXT NOT NULL,
    industry_segment TEXT NOT NULL,
    contracted_capacity_kw REAL NOT NULL CHECK (contracted_capacity_kw > 0),
    equipment_efficiency REAL NOT NULL CHECK (equipment_efficiency BETWEEN 0 AND 1)
);

CREATE TABLE IF NOT EXISTS load_measurements (
    facility_id TEXT NOT NULL REFERENCES facilities(facility_id),
    timestamp TEXT NOT NULL,
    gross_load_kw REAL,
    renewable_generation_kw REAL NOT NULL CHECK (renewable_generation_kw >= 0),
    net_load_kw REAL,
    temperature_c REAL NOT NULL,
    tariff_usd_kwh REAL NOT NULL CHECK (tariff_usd_kwh >= 0),
    is_weekend INTEGER NOT NULL CHECK (is_weekend IN (0, 1)),
    is_anomaly INTEGER NOT NULL CHECK (is_anomaly IN (0, 1)),
    quality_flag TEXT NOT NULL CHECK (quality_flag IN ('valid', 'anomaly', 'missing')),
    data_source TEXT NOT NULL CHECK (data_source = 'synthetic_generator_v1'),
    PRIMARY KEY (facility_id, timestamp)
);

CREATE INDEX IF NOT EXISTS idx_load_timestamp ON load_measurements(timestamp);
CREATE INDEX IF NOT EXISTS idx_load_quality ON load_measurements(quality_flag);

CREATE VIEW IF NOT EXISTS v_park_hourly_load AS
SELECT
    timestamp,
    SUM(gross_load_kw) AS gross_load_kw,
    SUM(renewable_generation_kw) AS renewable_generation_kw,
    SUM(net_load_kw) AS net_load_kw,
    AVG(temperature_c) AS temperature_c,
    AVG(tariff_usd_kwh) AS tariff_usd_kwh
FROM load_measurements
GROUP BY timestamp;

CREATE VIEW IF NOT EXISTS v_daily_facility_summary AS
SELECT
    facility_id,
    substr(timestamp, 1, 10) AS operating_date,
    AVG(net_load_kw) AS average_net_load_kw,
    MAX(net_load_kw) AS peak_net_load_kw,
    SUM(net_load_kw) AS energy_kwh,
    SUM(renewable_generation_kw) AS renewable_energy_kwh,
    SUM(is_anomaly) AS anomaly_count
FROM load_measurements
GROUP BY facility_id, substr(timestamp, 1, 10);
"""


def build_database(frame: pd.DataFrame, database_path: str | Path) -> Path:
    """Create a normalized SQLite database from the generated CSV-shaped frame."""
    database_path = Path(database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    if database_path.exists():
        database_path.unlink()

    with sqlite3.connect(database_path) as connection:
        connection.executescript(SCHEMA_SQL)
        connection.execute(
            "INSERT INTO dataset_metadata(key, value) VALUES (?, ?)",
            ("data_notice", DATA_NOTICE),
        )
        connection.execute(
            "INSERT INTO dataset_metadata(key, value) VALUES (?, ?)",
            ("generator_version", "synthetic_generator_v1"),
        )
        connection.execute(
            """
            INSERT INTO parks(park_id, park_name, region, timezone, data_classification)
            VALUES ('PARK-DEMO-01', 'Synthetic Industrial Park', 'Demonstration Region',
                    'America/New_York', 'synthetic')
            """
        )

        facilities = frame[
            [
                "facility_id",
                "park_id",
                "facility_type",
                "industry_segment",
                "contracted_capacity_kw",
                "equipment_efficiency",
            ]
        ].drop_duplicates()
        facilities.to_sql("facilities", connection, if_exists="append", index=False)
        frame[
            [
                "facility_id",
                "timestamp",
                "gross_load_kw",
                "renewable_generation_kw",
                "net_load_kw",
                "temperature_c",
                "tariff_usd_kwh",
                "is_weekend",
                "is_anomaly",
                "quality_flag",
                "data_source",
            ]
        ].to_sql("load_measurements", connection, if_exists="append", index=False)
        connection.execute("PRAGMA optimize")
    return database_path


def export_demo_assets(
    output_dir: str | Path = "data",
    days: int = 30,
    facilities_per_type: int = 4,
    seed: int = 42,
) -> tuple[Path, Path]:
    """Write the synthetic CSV and its query-ready SQLite representation."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    frame = generate_hourly_dataset(days, facilities_per_type, seed)
    csv_path = output_dir / "synthetic_hourly_loads.csv"
    db_path = output_dir / "industrial_load_demo.sqlite"
    frame.to_csv(csv_path, index=False)
    build_database(frame, db_path)
    return csv_path, db_path


def read_query(database_path: str | Path, query: str) -> pd.DataFrame:
    """Run a read-only SELECT query against the demo database."""
    if not query.lstrip().lower().startswith(("select", "with", "pragma")):
        raise ValueError("Only read-only SELECT, WITH, or PRAGMA queries are allowed")
    uri = f"file:{Path(database_path).resolve()}?mode=ro"
    with sqlite3.connect(uri, uri=True) as connection:
        return pd.read_sql_query(query, connection)


def main() -> None:
    """Console entry point for rebuilding the public demo assets."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="data")
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--facilities-per-type", type=int, default=4)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    csv_path, db_path = export_demo_assets(
        args.output_dir, args.days, args.facilities_per_type, args.seed
    )
    print(DATA_NOTICE)
    print(f"CSV: {csv_path}")
    print(f"SQLite: {db_path}")


if __name__ == "__main__":
    main()
