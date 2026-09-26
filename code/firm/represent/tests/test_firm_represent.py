import math
import pathlib
import sys

import numpy as np
import torch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_represent import encode, fine_tune, info_nce, linear_probe, pretrain_dae, pretrain_predictive


def test_info_nce_bounds():
    z = torch.zeros(8, 4)
    assert abs(float(info_nce(z, z)) - math.log(15)) < 1e-5            # uninformative codes: ln(2m - 1)
    torch.manual_seed(0)
    a = torch.nn.functional.normalize(torch.randn(8, 16), dim=1) * 10
    assert float(info_nce(a, a, tau=0.05)) < 0.01                       # identical views, well separated


def test_linear_dae_finds_the_principal_subspace():
    rng = np.random.default_rng(0)
    base = rng.standard_normal((3000, 2)) * [3.0, 2.0]
    X = np.c_[base, 0.1 * rng.standard_normal((3000, 4))].astype(np.float32)
    enc = pretrain_dae(X, code=2, hidden=(16,), mask=0.0, noise=0.0, epochs=30, seed=1)
    Z = encode(enc, X)
    fit = np.linalg.lstsq(np.c_[Z, np.ones(len(Z))], X[:, :2], rcond=None)[0]
    resid = X[:, :2] - np.c_[Z, np.ones(len(Z))] @ fit
    assert resid.var() / X[:, :2].var() < 0.1                         # the code holds the two large directions


def test_predictive_pretext_and_fine_tune_copy():
    rng = np.random.default_rng(1)
    X = rng.standard_normal((4000, 10)).astype(np.float32)
    Y = (X[:, :1] - X[:, 1:2]).astype(np.float32)                       # a label-free "future" of the input
    enc = pretrain_predictive(X, Y, code=4, hidden=(16,), epochs=15, seed=1)
    p = linear_probe(encode(enc, X[:3000]), Y[:3000, 0], encode(enc, X[3000:]))
    assert np.corrcoef(p, Y[3000:, 0])[0, 1] > 0.9
    before = [w.clone() for w in enc.parameters()]
    fine_tune(enc, X[:500], Y[:500, 0], X[500:600], Y[500:600, 0], epochs=3)
    assert all(torch.equal(a, b) for a, b in zip(before, enc.parameters(), strict=True))
