import sys
from pathlib import Path
import numpy as np, pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"src"))
from gems72 import metric as M
def test_published_example():
    assert M.dti(3.00, 1.89, 2.00) == pytest.approx(0.6026, abs=5e-4)
    assert round(M.dti(3.00, 1.89, 2.00),2)==0.60
def test_bruteforce_equivalence():
    rng=np.random.default_rng(0)
    for _ in range(4):
        pred=(rng.random((12,12))<0.12)*rng.random((12,12))
        truth=rng.random((12,12))<0.10
        c=M.components(pred,truth)
        # check FN+TP = K, FP = S-M
        assert c["FN_w"] == pytest.approx(c["K"]-c["TP_w"], abs=1e-9)
        assert c["FP_w"] == pytest.approx(c["S"]-c["M"], abs=1e-9)
def test_marginal_threshold_exact():
    truth=np.zeros((25,25),bool); truth[10,10]=True
    for d in range(1,6):
        pred=np.zeros((25,25)); pred[20,20]=1.0
        before=M.score(pred, truth); k=M.kernel(d); cand=pred.copy(); cand[10,10+d]=1.0
        after=M.score(cand, truth)
        assert (after>before)==(k>M.ALPHA*before), (d,k,before,after)
def test_far_mass_harmful():
    truth=np.zeros((21,21),bool); truth[10,3:18]=True
    pred=np.zeros((21,21)); pred[10,5:15]=1.0
    before=M.score(pred, truth); cand=pred.copy(); cand[10,20]=1.0
    assert M.score(cand, truth) < before
