"""Low-latency inference (One Quant Book 12, chapter 26).

The forest (300 trees) and the multilayer perceptron of firm.mlinfer's fixture, fitted to a synthetic 16-feature
problem: their accuracy as float models and as int8 models quantised after training or with quantisation-aware
fine-tuning, and the Python side of the parity checks. Latencies are in bench_infer.py, measured once on the author's
laptop and never asserted."""
from __future__ import annotations

import copy
import functools
import os
import pathlib
import sys

for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np  # noqa: E402
import torch  # noqa: E402
from scipy.stats import spearmanr  # noqa: E402

_FIRM = pathlib.Path(__file__).resolve().parents[3] / "firm"
sys.path.insert(0, str(_FIRM / "mlinfer"))
import firm_mlinfer as mi  # noqa: E402
import make_mlinfer_fixture as fx  # noqa: E402


@functools.lru_cache(maxsize=1)
def models():
    forest, mlp, X, y = fx.models()
    qat = mi.fit_mlp(copy.deepcopy(mlp), X, y, epochs=10, seed=1, qat=True, lr=1e-3)
    return forest, mlp, qat, X


@functools.lru_cache(maxsize=1)
def test_data():
    return fx.problem(seed=5, n=20000)


def ic(p, y):
    return float(spearmanr(p, y)[0])


@functools.lru_cache(maxsize=1)
def accuracy(bits=(8, 6, 4)):
    """Rank IC on 20,000 new observations: the forest, the float MLP, and the MLP quantised to 8, 6 and 4 bits after
    training (PTQ) and after ten epochs of quantisation-aware fine-tuning at that width (QAT); and, at 8 bits, the
    integer model's error relative to its float version."""
    import make_mlinfer_fixture as fx

    forest, mlp, _, _ = models()
    _, _, X, y = fx.models()
    Xt, yt = test_data()
    with torch.no_grad():
        f32 = mlp(torch.as_tensor(Xt, dtype=torch.float32)).numpy()
    out = {"forest": ic(forest.predict(Xt), yt), "MLP float": ic(f32, yt)}
    for b in bits:
        ptq = mi.int8_forward(mi.quantise(mlp, X[:2000], b), Xt)
        qm = mi.fit_mlp(copy.deepcopy(mlp), X, y, epochs=10, seed=1, qat=True, lr=1e-3, bits=b)
        out[b] = (ic(ptq, yt), ic(mi.int8_forward(mi.quantise(qm, X[:2000], b), Xt), yt))
        if b == 8:
            out["ptq error"] = float(np.sqrt(np.mean((ptq - f32) ** 2)) / f32.std())
    return out


def parity_python():
    """The exported forest walked in Python against LightGBM, on the fixture's vectors."""
    forest, *_ = models()
    V = np.loadtxt(_FIRM / "mlinfer" / "data" / "vectors.csv", delimiter=",")
    f = mi.read_forest(_FIRM / "mlinfer" / "data" / "forest.txt")
    return float(np.abs(mi.forest_predict(f, V[:, :16]) - forest.predict(V[:, :16])).max())


def sizes():
    forest, *_ = models()
    f = mi.export_forest(forest)
    q = mi.quantise(models()[1], models()[3][:2000])
    return {"trees": len(f["roots"]), "splits": len(f["feature"]), "leaves": len(f["value"]),
            "mlp int8 bytes": int(sum(L["W"].size + 4 * L["B"].size for L in q["layers"])),
            "mlp float bytes": int(sum(4 * (L["W"].size + L["B"].size) for L in q["layers"]))}


def per_channel_ic(bits=4):
    """Exercise 7: post-training quantisation with one weight scale per output unit (row) instead of per tensor,
    simulated in floating point on the integer grid; rank IC on the test data."""
    import make_mlinfer_fixture as fx

    _, mlp, _, _ = models()
    _, _, X, _ = fx.models()
    Xt, yt = test_data()
    qm = 2 ** (bits - 1) - 1
    with torch.no_grad():
        h = torch.as_tensor(X[:2000], dtype=torch.float32)
        scales = [float(h.abs().max()) / qm]
        for i, lin in enumerate((mlp.l1, mlp.l2, mlp.l3)):
            h = lin(h)
            if i < 2:
                h = torch.relu(h)
                scales.append(float(h.abs().max()) / qm)
    x = np.clip(np.round(Xt / scales[0]), -qm, qm)
    for i, lin in enumerate((mlp.l1, mlp.l2, mlp.l3)):
        w = lin.weight.detach().numpy().astype(np.float64)
        sw = np.abs(w).max(axis=1, keepdims=True) / qm
        W = np.clip(np.round(w / sw), -qm, qm)
        acc = x @ W.T + np.round(lin.bias.detach().numpy() / (scales[i] * sw[:, 0]))
        y = acc * scales[i] * sw[:, 0]
        if i < 2:
            x = np.clip(np.round(np.maximum(y, 0) / scales[i + 1]), -qm, qm)
        else:
            return ic(y[:, 0], yt)
    return None
