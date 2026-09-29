"""Numbers gate: every number printed in Book 14, chapter 5 (text and solutions)."""
import functools
import pathlib
import sys

import numpy as np
import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "python"))
import nw_capture as c  # noqa: E402

wc = c.wc


@functools.lru_cache
def run(speed=1.0):
    rec, truth = c.session(speed=speed)
    return rec, truth, c.analyse(rec)


def test_budget_numbers():
    rows = {r["stage"]: r for r in c.budget_rows()}
    soft = ("decode", "ring", "book", "strategy", "risk", "gateway")
    assert sum(round(rows[s]["p50"]) for s in soft) == 1528
    st = {s.name: s for s in c.stages()}
    assert round(st["network in"].p50_ns) == 263 and round(st["network out"].p50_ns) == 295
    assert sum(st[s].p50_ns for s in soft) == 1528 and sum(s.p50_ns for s in st.values()) == pytest.approx(3685, abs=1)
    assert round(rows["wire-to-wire"]["p50"] / 1000, 1) == 4.4 and round(rows["wire-to-wire"]["p99"] / 1000) == 35
    assert round(rows["ring"]["p99"] / 1000) == 32 and round(rows["card receive"]["p50"], -1) == 800
    half = c.budget_rows(card=2)[-1]
    assert round(half["p50"] / 1000, 2) == 3.47 and round(rows["wire-to-wire"]["p50"] / 1000, 2) == 4.39
    assert round((rows["wire-to-wire"]["p50"] - half["p50"]) / 1000, 1) == 0.9
    assert round((263 + 295) / 1000, 2) == 0.56


def test_by_hand():
    assert 16_771 - 12_345 == 4426
    fps = 4e9 / (220 * 8)
    assert round(fps / 1e6, 2) == 2.27 and round(fps * 232 / 1e6) == 527 and round(2 * fps * 232 / 1e9, 2) == 1.05
    assert round(99_055 * 0.002 ** 2, 1) == 0.4
    assert round((4407 - 1528) / 1000, 1) == 2.9


@pytest.mark.reference
def test_session_numbers():
    rec, truth, a = run()
    assert a["n_packets"] == 99_055 and a["n_orders"] == 9_558 and len(truth) == 9_558
    assert np.allclose(np.sort(a["w2w"]), np.sort([t - s for t, _, s in truth]))           # exact pairing
    q = np.quantile(a["w2w"], [0.5, 0.99])
    assert round(q[0] / 1000, 1) == 4.4 and round(q[1] / 1000) == 38 and round(31.9 / (q[1] / 1000), 2) == 0.83
    assert round(100 * a["nearest_wrong"]) == 47
    assert round(np.quantile(a["w2w_naive"], 0.5) / 1000, 1) == 3.5 and round(np.quantile(a["w2w_naive"], 0.99) / 1000) == 27
    assert (a["gaps_a"], a["gaps_b"], a["both"]) == (158, 198, 0)
    assert round(a["peak_100us_gbps"], 2) == 1.24 and round(a["mean_gbps"], 2) == 0.14 and round(1.24 / 0.14) == 9
    _, _, a4 = run(4.0)
    assert round(100 * a4["nearest_wrong"]) == 25                                                  # exercise 7


@pytest.mark.reference
def test_disk(tmp_path):
    rec, _, _ = run()
    wc.write_pcap(tmp_path / "s.pcap", rec)
    size = (tmp_path / "s.pcap").stat().st_size
    assert round(size / 1e6) == 38 and round(size * 3600 / 1e9) == 138


def test_small_runs():
    rec, truth = c.session(seconds=0.05)
    a = c.analyse(rec)
    assert a["n_orders"] == len(truth) > 0
    assert np.allclose(np.sort(a["w2w"]), np.sort([t - s for t, _, s in truth]))
    assert np.median(a["w2w_naive"]) <= np.median(a["w2w"])
