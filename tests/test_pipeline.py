import numpy as np
import sqlite3

from industrial_load.data import generate_park_data
from industrial_load.database import DATA_NOTICE, build_database, generate_hourly_dataset
from industrial_load.dtw import dtw_distance
from industrial_load.pipeline import OptimizedLoadClusterer, evaluate


def test_dtw_identity_and_symmetry():
    a = np.array([0.0, 1.0, 2.0])
    b = np.array([0.0, 0.8, 2.1])
    assert dtw_distance(a, a) == 0
    assert np.isclose(dtw_distance(a, b), dtw_distance(b, a))


def test_pipeline_is_reproducible_and_finds_structure():
    frame, truth = generate_park_data(n_per_class=10, seed=7)
    loads = frame.filter(like="load_h").to_numpy()
    context = frame[["temperature_c", "tariff_usd_kwh", "renewable_policy_index", "equipment_efficiency"]].to_numpy()
    a = OptimizedLoadClusterer(random_state=7).fit_predict(loads, context)
    b = OptimizedLoadClusterer(random_state=7).fit_predict(loads, context)
    assert np.array_equal(a.labels, b.labels)
    assert 2 <= a.n_clusters <= 6
    assert evaluate(truth, a.labels) > 0.35


def test_synthetic_dataset_and_database(tmp_path):
    frame = generate_hourly_dataset(days=2, facilities_per_type=1, seed=42)
    assert len(frame) == 3 * 2 * 24
    assert set(frame["data_source"]) == {"synthetic_generator_v1"}
    assert set(frame["facility_type"]) == {
        "energy_intensive",
        "distributed_energy",
        "ev_charging",
    }

    database_path = build_database(frame, tmp_path / "demo.sqlite")
    with sqlite3.connect(database_path) as connection:
        notice = connection.execute(
            "SELECT value FROM dataset_metadata WHERE key = 'data_notice'"
        ).fetchone()[0]
        measurement_count = connection.execute(
            "SELECT COUNT(*) FROM load_measurements"
        ).fetchone()[0]
        view_count = connection.execute(
            "SELECT COUNT(*) FROM v_park_hourly_load"
        ).fetchone()[0]
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]

    assert notice == DATA_NOTICE
    assert measurement_count == len(frame)
    assert view_count == 48
    assert integrity == "ok"
