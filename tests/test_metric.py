"""Tests for src/metric.py.

Verifies the distance-weighted Tversky index against:
  1. A tiny fully hand-computable grid (exact expected value derived by hand).
  2. The published worked-example arithmetic:
     TPw=3.00, FPw=1.89, FNw=2.00, alpha=0.2, beta=0.8 -> DTI ~= 0.60.
"""

import numpy as np
import pytest

from src.metric import distance_weighted_tversky, ALPHA, BETA, R_M


def test_published_worked_example_arithmetic():
    """The problem page's worked example: 3.00 / (3.00 + 0.2*1.89 + 0.8*2.00) = 0.6026.. ~= 0.60."""
    tpw, fpw, fnw = 3.00, 1.89, 2.00
    expected = tpw / (tpw + ALPHA * fpw + BETA * fnw)
    assert abs(expected - 0.60) < 0.01


def test_single_prediction_covers_single_ground_truth_perfectly():
    """One GT pixel, one predicted pixel at same location, p=1 -> DTI=1."""
    h = w = 5
    p = np.zeros((h, w))
    gt = np.zeros((h, w))
    p[2, 2] = 1.0
    gt[2, 2] = 1.0
    res = distance_weighted_tversky(p, gt, pixel_size=1.0, R=3.0)
    assert res["n_gt"] == 1 and res["n_pred"] == 1
    assert abs(res["TPw"] - 1.0) < 1e-9
    assert abs(res["FPw"]) < 1e-9
    assert abs(res["FNw"]) < 1e-9
    assert abs(res["DTI"] - 1.0) < 1e-9


def test_hand_computed_two_ground_truths():
    """5x5 grid, pixel_size=1, R=3.
    GT at (0,0) and (4,4); single prediction p=1 at (2,2).
    d = sqrt(8) = 2.828 <= 3 -> k = 1 - 2.828/3 = 0.05725.
    TPw = 2*0.05725 = 0.1145
    FNw = 2 - 0.1145 = 1.8855
    FPw = 1*(1 - 0.05725) = 0.94275
    DTI = 0.1145 / (0.1145 + 0.2*0.94275 + 0.8*1.8855) = 0.06327
    """
    h = w = 5
    p = np.zeros((h, w))
    gt = np.zeros((h, w))
    p[2, 2] = 1.0
    gt[0, 0] = 1.0
    gt[4, 4] = 1.0
    res = distance_weighted_tversky(p, gt, pixel_size=1.0, R=3.0)
    d = np.sqrt(8.0)
    k = 1.0 - d / 3.0
    tpw_expected = 2 * k
    fnw_expected = 2 - tpw_expected
    fpw_expected = 1.0 * (1.0 - k)
    dti_expected = tpw_expected / (tpw_expected + ALPHA * fpw_expected + BETA * fnw_expected)
    assert res["n_gt"] == 2 and res["n_pred"] == 1
    assert abs(res["TPw"] - tpw_expected) < 1e-9
    assert abs(res["FNw"] - fnw_expected) < 1e-9
    assert abs(res["FPw"] - fpw_expected) < 1e-9
    assert abs(res["DTI"] - dti_expected) < 1e-9


def test_uncovered_ground_truth_gives_dti_zero():
    """GT far from any prediction -> TPw=0, FNw=n_gt -> DTI=0."""
    h = w = 5
    p = np.zeros((h, w))
    gt = np.zeros((h, w))
    p[0, 0] = 1.0
    gt[4, 4] = 1.0  # distance sqrt(32)=5.66 > R=3 -> uncovered
    res = distance_weighted_tversky(p, gt, pixel_size=1.0, R=3.0)
    assert abs(res["TPw"]) < 1e-9
    assert abs(res["FNw"] - 1.0) < 1e-9
    assert abs(res["DTI"]) < 1e-9


def test_no_ground_truth_any_prediction_is_fp():
    """No GT, some prediction -> DTI=0 (all FP)."""
    h = w = 5
    p = np.ones((h, w)) * 0.5
    gt = np.zeros((h, w))
    res = distance_weighted_tversky(p, gt, pixel_size=1.0, R=3.0)
    assert abs(res["DTI"]) < 1e-9
    assert res["n_gt"] == 0


def test_values_outside_range_rejected():
    h = w = 5
    p = np.ones((h, w)) * 1.5
    gt = np.zeros((h, w))
    with pytest.raises(ValueError):
        distance_weighted_tversky(p, gt)


def test_nan_rejected():
    h = w = 5
    p = np.full((h, w), np.nan)
    gt = np.zeros((h, w))
    with pytest.raises(ValueError):
        distance_weighted_tversky(p, gt)


def test_shape_mismatch_rejected():
    p = np.ones((4, 4))
    gt = np.ones((5, 5))
    with pytest.raises(ValueError):
        distance_weighted_tversky(p, gt)
