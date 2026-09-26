import pathlib
import sys

import numpy as np
import torch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tape"))
from firm_lobseq import CNN, TCN, Attention, LSTMNet, Scaler, evaluate, snapshots, train, windows
from firm_tape import Book, TapeConfig, simulate


def test_snapshots_use_no_later_message():
    tape = simulate(TapeConfig(seconds=120, news_at=None, seed=5))
    times, S, mid = snapshots(tape, step=1.0, levels=5, start=30.0)
    b = Book()
    for row in tape.msgs[tape.msgs["t"] <= times[10]]:
        b.apply(row)
    bids, asks = b.depth(1, 5), b.depth(-1, 5)
    m = 0.5 * (bids[0][0] + asks[0][0])
    assert mid[10] == m and S[10, 0] == m - bids[0][0] and S[10, 2] == asks[0][0] - m
    assert np.isclose(S[10, 1], np.log1p(bids[0][1] / tape.cfg.lot))


def test_windows_and_labels_by_hand():
    S = np.arange(12, dtype=np.float32).reshape(6, 2)
    mid = np.array([0.0, 0.0, 1.0, 1.0, -1.0, 0.0])
    X, y, fut, idx = windows(S, mid, T=2, horizon=2, threshold=0.25)
    assert list(idx) == [1, 2, 3] and X.shape == (3, 2, 2) and np.array_equal(X[0], S[0:2])
    assert np.allclose(fut, [1.0, -1.0, -1.5]) and list(y) == [2, 0, 0]
    sc = Scaler().fit(X)
    assert np.allclose(sc.transform(X).reshape(-1, 2).mean(axis=0), 0, atol=1e-6)


def test_tcn_is_causal():
    torch.manual_seed(0)
    net = TCN(3)
    x = torch.randn(1, 12, 3)
    x2 = x.clone()
    x2[0, 8:] += 5.0                                                    # change the future of step 7
    z1 = net.inp(x.transpose(1, 2))
    z2 = net.inp(x2.transpose(1, 2))
    for b in net.blocks:
        z1 = z1 + torch.relu(b(z1))
        z2 = z2 + torch.relu(b(z2))
    assert torch.allclose(z1[:, :, :8], z2[:, :, :8])


def test_models_learn_a_planted_pattern():
    rng = np.random.default_rng(0)
    X = rng.standard_normal((1200, 10, 4)).astype(np.float32)
    s = X[:, -1, 0] + X[:, -2, 1]
    y = np.where(s > 0.5, 2, np.where(s < -0.5, 0, 1))
    for net in (CNN(4), LSTMNet(4), TCN(4), Attention(4, 10)):
        torch.manual_seed(0)
        m, _, _ = train(net, X[:900], y[:900], X[900:1000], y[900:1000], epochs=25, lr=3e-3, patience=6)
        res = evaluate(m, X[1000:], y[1000:], s[1000:])
        assert res["accuracy"] > 0.5 and res["ic"] > 0.4
