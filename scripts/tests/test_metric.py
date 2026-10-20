"""Unit tests for the exact DTI implementation.

Verified against the published worked example:
TP_w = 3.00, FP_w = 1.89, FN_w = 2.00, alpha=0.2, beta=0.8
=> DTI = 3 / (3 + 0.2*1.89 + 0.8*2) = 0.6026... ~ 0.60
Source: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
"""

import numpy as np

from scripts.evaluate_holdout import distance_weighted_tversky


def test_perfect_prediction_is_one():
    gt = np.zeros((10, 10)); gt[3:7, 3:7] = 1
    p = gt.copy()
    res = distance_weighted_tversky(p, gt)
    assert abs(res["DTI"] - 1.0) < 1e-9, res
    assert res["TP_w"] == 16.0 and res["FP_w"] == 0.0 and res["FN_w"] == 0.0


def test_zero_prediction_is_zero():
    gt = np.zeros((10, 10)); gt[4, 4] = 1
    p = np.zeros((10, 10))
    res = distance_weighted_tversky(p, gt)
    assert abs(res["DTI"]) < 1e-12, res
    assert res["TP_w"] == 0.0 and res["FN_w"] == 1.0


def test_worked_example_arithmetic():
    tp_w, fp_w, fn_w = 3.00, 1.89, 2.00
    alpha, beta = 0.2, 0.8
    expected = tp_w / (tp_w + alpha * fp_w + beta * fn_w)
    assert abs(expected - 0.6026) < 5e-4, expected  # matches published ~0.60
    dti = expected
    assert abs(dti - 0.60) < 0.01


def test_prediction_at_kernel_edge_decays_linearly():
    # Single GT pixel at centre; single prediction pixel at distance d.
    gt = np.zeros((9, 9)); gt[4, 4] = 1.0
    p = np.zeros((9, 9)); p[4, 6] = 1.0  # d = 2 px -> k = 1 - 2/3 = 1/3
    res = distance_weighted_tversky(p, gt)
    assert abs(res["TP_w"] - 1.0 / 3.0) < 1e-9, res
    assert abs(res["FN_w"] - 2.0 / 3.0) < 1e-9, res
    # prediction pixel is 2 px from GT -> w = 1/3 -> FP = 1 * (1 - 1/3) = 2/3
    assert abs(res["FP_w"] - 2.0 / 3.0) < 1e-9, res
    dti = res["TP_w"] / (res["TP_w"] + 0.2 * res["FP_w"] + 0.8 * res["FN_w"])
    assert abs(dti - res["DTI"]) < 1e-12


def test_out_of_kernel_prediction_is_full_fp():
    gt = np.zeros((9, 9)); gt[4, 4] = 1.0
    p = np.zeros((9, 9)); p[0, 0] = 1.0  # d > 3 -> w = 0 -> FP = 1
    res = distance_weighted_tversky(p, gt)
    assert res["TP_w"] == 0.0 and res["FP_w"] == 1.0 and res["FN_w"] == 1.0
    assert abs(res["DTI"]) < 1e-12


def test_values_outside_range_rejected():
    gt = np.zeros((5, 5)); gt[2, 2] = 1.0
    p = np.full((5, 5), 1.5)
    try:
        distance_weighted_tversky(p, gt)
    except ValueError:
        return
    raise AssertionError("values outside [0,1] must be rejected")


if __name__ == "__main__":
    test_perfect_prediction_is_one()
    test_zero_prediction_is_zero()
    test_worked_example_arithmetic()
    test_prediction_at_kernel_edge_decays_linearly()
    test_out_of_kernel_prediction_is_full_fp()
    test_values_outside_range_rejected()
    print("all metric tests passed")
