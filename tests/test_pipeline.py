import numpy as np

from industrial_load.data import generate_park_data
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

