import numpy as np
import pytest

from industrial_load.data import _daily_profile, generate_park_data
from industrial_load.pipeline import MinMaxContext
from industrial_load.preprocessing import LoadPreprocessor


def test_daily_profile_rejects_unknown_type():
    with pytest.raises(ValueError, match="Unknown profile type"):
        _daily_profile("unknown", np.arange(24), np.random.default_rng(1))


def test_profile_generator_shape_labels_corruption_and_reproducibility():
    first, labels_a = generate_park_data(
        n_per_class=2, periods=12, seed=3, anomaly_rate=0, missing_rate=0.1
    )
    second, labels_b = generate_park_data(
        n_per_class=2, periods=12, seed=3, anomaly_rate=0, missing_rate=0.1
    )
    assert first.shape == (6, 17)
    assert np.array_equal(labels_a, labels_b)
    assert first.equals(second)
    assert first.filter(like="load_h").isna().any().any()


def test_preprocessor_repairs_missing_outliers_and_scales():
    values = np.array(
        [
            [1.0, 5.0, 10.0],
            [1.1, np.nan, 10.0],
            [0.9, 5.2, 10.0],
            [50.0, 4.8, 10.0],
            [1.0, 5.1, 10.0],
            [1.2, 5.0, 10.0],
        ]
    )
    processor = LoadPreprocessor(n_neighbors=2, outlier_z=2.5)
    transformed = processor.fit_transform(values)
    assert processor.repaired_count_ >= 2
    assert np.isfinite(transformed).all()
    assert transformed.min() >= -1e-12
    assert transformed.max() <= 1 + 1e-12


def test_context_scaling_handles_missing_and_constant_columns():
    context = np.array([[1.0, 5.0], [np.nan, 5.0], [3.0, 5.0]])
    scaled = MinMaxContext().fit_transform(context)
    assert np.isfinite(scaled).all()
    assert np.allclose(scaled[:, 1], 0)
    assert np.all((scaled[:, 0] >= 0) & (scaled[:, 0] <= 1))
