import pathlib
import sys

import numpy as np
import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "cagenet"))
import firm_cagenet as cg  # noqa: E402
import firm_wirepath as wp  # noqa: E402


def test_stage_fit_hits_its_quantiles():
    s = wp.Stage("x", 1000, 3000)
    x = s.sample(np.random.default_rng(1), 400_000)
    assert np.quantile(x, 0.5) == pytest.approx(1000, rel=0.01) and np.quantile(x, 0.99) == pytest.approx(3000, rel=0.02)
    assert np.all(wp.Stage("c", 250, 0).sample(np.random.default_rng(1), 5) == 250)


def test_book13_stages_are_read():
    st = wp.book13_software()
    assert [s.name for s in st] == list(wp.SOFTWARE) and all(s.p99_ns >= s.p50_ns > 0 for s in st)


def test_wire_stages_and_report():
    D, C = cg.Device, cg.Cable
    cage = cg.Cage([D("A", "handoff"), D("O", "handoff"), D("l1", "l1", 4), D("mx", "mux", 39), D("s", "server")],
                   [C("A", "l1", 30), C("l1", "s", 3), C("s", "mx", 3), C("mx", "O", 30)])
    w = wp.wire_stages(cage, cage.path("A", "s"), cage.path("s", "O"))
    assert w[0].p50_ns == pytest.approx(cage.latency_ns(["A", "l1", "s"], 104, 10.0))
    stages = w + wp.card_stages(700, 1500, 700, 1500) + [wp.hardware_stage(40, 322.265625)]
    rows = wp.report(stages, n=20_000)
    total = rows[-1]
    assert total["stage"] == "wire-to-wire" and total["p50"] > sum(r["p50"] for r in rows[:-1]) * 0.9
    assert rows[-2]["p50"] == pytest.approx(40 * 1000 / 322.265625)
