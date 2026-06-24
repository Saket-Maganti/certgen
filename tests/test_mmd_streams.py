import sys

import numpy as np
import pytest

from certgen.metrics.kernels import linear_kernel, polynomial_kernel, rbf_kernel
from certgen.metrics.mmd import unbiased_mmd2
from certgen.metrics.streams import clip_stream_values, mmd_difference_stream


def test_kernel_shape_validation():
    x = np.zeros((4, 2))
    y = np.zeros((5, 2))
    assert linear_kernel(x, y).shape == (4, 5)
    assert polynomial_kernel(x, y).shape == (4, 5)
    assert rbf_kernel(x, y).shape == (4, 5)
    with pytest.raises(ValueError):
        linear_kernel(np.zeros(4), y)


def test_mmd_quadratic_diagnostics():
    x = np.zeros((8, 2))
    y = np.ones((8, 2))
    assert unbiased_mmd2(x, x) == 0.0
    assert unbiased_mmd2(x, y) > 0


def test_mmd_difference_stream_direction_a_closer_and_b_closer():
    r = np.tile(np.array([[1.0, 0.0]]), (12, 1))
    a_close = r + 0.01
    b_far = np.tile(np.array([[0.0, 1.0]]), (12, 1))
    stream = mmd_difference_stream(a_close, b_far, r, {"name": "rbf", "normalize": "l2"}, seed=1)
    assert stream.mean() < 0
    reverse = mmd_difference_stream(b_far, a_close, r, {"name": "rbf", "normalize": "l2"}, seed=1)
    assert reverse.mean() > 0


def test_mmd_difference_stream_is_deterministic_with_seed():
    rng = np.random.default_rng(0)
    r = rng.normal(size=(20, 3))
    a = r + 0.01
    b = r + 0.3
    first = mmd_difference_stream(a, b, r, {"name": "rbf", "normalize": "l2"}, seed=7)
    second = mmd_difference_stream(a, b, r, {"name": "rbf", "normalize": "l2"}, seed=7)
    assert first.values == second.values


def test_stream_shape_validation_and_no_heavy_imports():
    with pytest.raises(ValueError):
        mmd_difference_stream(np.zeros((3, 2)), np.zeros((3, 2)), np.zeros((3, 2)), {"name": "polynomial"})
    assert "torch" not in sys.modules


def test_clip_stream_metadata():
    clipped = clip_stream_values([-2.0, -0.5, 0.2, 2.5], -1.0, 1.0)
    assert clipped.values == [-1.0, -0.5, 0.2, 1.0]
    assert clipped.metadata["num_clipped_low"] == 1
    assert clipped.metadata["num_clipped_high"] == 1
    assert clipped.metadata["fraction_clipped"] == 0.5
