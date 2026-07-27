import sqlite3

import pytest

from industrial_load.database import (
    DATA_NOTICE,
    build_database,
    export_demo_assets,
    generate_hourly_dataset,
    read_query,
)


@pytest.mark.parametrize(
    ("days", "facilities"),
    [(0, 1), (1, 0), (-1, 1)],
)
def test_generator_rejects_non_positive_dimensions(days, facilities):
    with pytest.raises(ValueError, match="must be positive"):
        generate_hourly_dataset(days=days, facilities_per_type=facilities)


def test_synthetic_dataset_is_reproducible_and_labeled():
    first = generate_hourly_dataset(days=1, facilities_per_type=1, seed=42)
    second = generate_hourly_dataset(days=1, facilities_per_type=1, seed=42)
    assert first.equals(second)
    assert len(first) == 3 * 24
    assert set(first["data_source"]) == {"synthetic_generator_v1"}
    assert set(first["facility_type"]) == {
        "energy_intensive",
        "distributed_energy",
        "ev_charging",
    }
    assert (first["renewable_generation_kw"] >= 0).all()


def test_database_integrity_metadata_views_indexes_and_foreign_keys(tmp_path):
    frame = generate_hourly_dataset(days=2, facilities_per_type=1, seed=42)
    database_path = build_database(frame, tmp_path / "demo.sqlite")
    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute(
            "SELECT value FROM dataset_metadata WHERE key = 'data_notice'"
        ).fetchone()[0] == DATA_NOTICE
        assert connection.execute("SELECT COUNT(*) FROM facilities").fetchone()[0] == 3
        assert connection.execute(
            "SELECT COUNT(*) FROM load_measurements"
        ).fetchone()[0] == len(frame)
        assert connection.execute(
            "SELECT COUNT(*) FROM v_park_hourly_load"
        ).fetchone()[0] == 48
        assert connection.execute(
            "SELECT COUNT(*) FROM v_daily_facility_summary"
        ).fetchone()[0] == 6
        indexes = {
            row[1]
            for row in connection.execute("PRAGMA index_list('load_measurements')")
        }
        assert {"idx_load_timestamp", "idx_load_quality"} <= indexes
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO load_measurements(
                    facility_id, timestamp, renewable_generation_kw,
                    temperature_c, tariff_usd_kwh, is_weekend, is_anomaly,
                    quality_flag, data_source
                ) VALUES ('missing-facility', '2026-01-01T00:00:00', 0, 0, 0,
                          0, 0, 'valid', 'synthetic_generator_v1')
                """
            )


def test_export_and_read_only_query(tmp_path):
    csv_path, database_path = export_demo_assets(
        tmp_path, days=1, facilities_per_type=1, seed=9
    )
    assert csv_path.exists()
    assert database_path.exists()
    summary = read_query(
        database_path,
        "WITH counts AS (SELECT COUNT(*) AS n FROM load_measurements) SELECT n FROM counts",
    )
    assert int(summary.iloc[0]["n"]) == 72
    pragma = read_query(database_path, "PRAGMA integrity_check")
    assert pragma.iloc[0, 0] == "ok"
    with pytest.raises(ValueError, match="read-only"):
        read_query(database_path, "DELETE FROM load_measurements")
