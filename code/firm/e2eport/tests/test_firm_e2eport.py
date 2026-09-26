import pathlib
import sys

import numpy as np
import torch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_e2eport import char_panel, least_squares, mv_layer, run, train_decision  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "portcons"))
from firm_portcons import Problem  # noqa: E402


def test_layer_matches_portcons_without_costs():
    rng = np.random.default_rng(0)
    mu = rng.normal(0, 0.001, 20)
    w = mv_layer(mu, np.zeros(20), 0.0, 20.0, 0.03)
    res = Problem(mu, np.zeros((20, 1)), np.zeros((1, 1)), np.full(20, 0.03**2), 20.0, np.zeros(20)).solve()
    assert np.allclose(w, res["w"], atol=1e-6)


def test_layer_gradient_matches_finite_differences():
    mu = torch.tensor([0.001, -0.002], requires_grad=True)
    w = mv_layer(mu, torch.tensor([0.1, 0.0]), 0.0005, 20.0, 0.03)
    w.sum().backward()
    h = 1e-7
    fd = (mv_layer(0.001 + h, 0.1, 0.0005) - mv_layer(0.001, 0.1, 0.0005)) / h
    assert abs(float(mu.grad[0]) - fd) < 1e-3 * abs(fd)


def test_costs_charged_on_changes():
    X = np.ones((3, 2, 1))
    R = np.zeros((3, 2))
    r0 = run(np.array([0.0]), X, R + 0.01 * np.array([[1, -1], [1, 1], [-1, 1]]), np.array([True, False]), cost=0.0)
    assert r0["turnover"] == 0.0
    r1 = run(np.array([0.001]), X, R + 0.0, np.array([True, True]), cost=0.001)
    assert r1["turnover"] > 0


def test_decision_training_recovers_direction():
    d = char_panel(0, T=600, N=100)
    init = least_squares(d["X"], d["R"])
    b = train_decision(d["X"], d["R"], d["tradeable"], init, epochs=10)
    cos = b[1] / np.linalg.norm(b)
    assert cos > 0.8 and abs(b[0]) < abs(init[0])
