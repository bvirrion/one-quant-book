"""Numbers gate, Book 13 chapter 13."""
import csv
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE / "python"))
import ll_tuning as t  # noqa: E402

FIG = ROOT / "figdata/low-latency/13-linux-tuning"


def rows(name, key):
    with open(FIG / name, newline="", encoding="utf8") as f:
        return {r[key]: r for r in csv.DictReader(f)}


def test_proposition_on_simple_gaps():
    g = [500.0, 2000.0, 90.0]
    assert t.stolen_fraction(g, 10_000) == 0.259
    assert t.mean_wait(g, 10_000) == (500**2 + 2000**2 + 90**2) / 20_000
    assert t.p_wait_exceeds(g, 10_000, 1000) == 0.1
    # Monte Carlo check of the proposition on one gap layout
    import numpy as np
    rng = np.random.default_rng(1)
    starts = np.array([1000.0, 4000.0, 8000.0])
    arr = rng.uniform(0, 10_000, 400_000)
    w = np.zeros_like(arr)
    for s, gg in zip(starts, g, strict=True):
        inside = (arr >= s) & (arr < s + gg)
        w[inside] = s + gg - arr[inside]
    assert abs(w.mean() - t.mean_wait(g, 10_000)) < 2 and abs((w > 1000).mean() - 0.1) < 0.003


def test_exercises():
    tick = t.periodic(1000, 2000)
    assert round(t.stolen_fraction(tick, 1e9), 6) == 0.002 and round(t.mean_wait(tick, 1e9), 6) == 2.0     # ex. 1
    assert 3 << 30 > 67108864                                                                           # ex. 2
    assert [c + 32 for c in range(12, 16)] == [44, 45, 46, 47]                                          # ex. 3
    short, long_ = t.periodic(1000, 10_000), t.periodic(1, 1e7)
    assert t.stolen_fraction(short, 1e9) == t.stolen_fraction(long_, 1e9) == 0.01                        # ex. 4
    assert t.mean_wait(short, 1e9) == 50 and t.mean_wait(long_, 1e9) == 50_000
    assert t.p_wait_exceeds(short, 1e9, 5000) == 0.005 and round(t.p_wait_exceeds(long_, 1e9, 5000), 6) == 0.009995
    assert t.rt_throttle_gap() == 50e6 and t.rt_throttle_gap() / 1e9 == 0.05                             # ex. 6


def test_problem_model():
    p = t.problem()
    assert p["tick_fraction"] == 0.0005 and p["tick_mean_wait"] == 0.5 and p["tick_p_wait_1us"] == 0.00025
    assert p["tuned_fraction"] == 2e-6 and p["tuned_mean_wait"] == 0.002
    assert p["throttle_gap_ms"] == 50 and p["throttle_fraction"] == 0.05
    assert t.wait_quantile(t.periodic(1000, 10_000), 1e9, 0.999) == 9000
    assert t.share_of_cpu(2) == 0.5


def test_measured_hiccups():
    s = rows("measured_hiccup_summary.csv", "scenario")
    alone, shared = s["alone"], s["shared"]
    ns_per_pass = float(alone["seconds"]) * 1e9 / float(alone["loops"])
    assert round(ns_per_pass) == 15                                                 # about fifteen ns a pass
    assert round(float(alone["loops"]) / 1e6) == 323                               # problem, question 2
    assert round(float(alone["stolen_fraction"]), 3) == 0.013                        # about 1.3%
    assert round(float(alone["worst_ns"]) / 1e5) == 54                               # ~5.4 ms
    assert round(float(alone["mean_wait_ns"]) / 100) == 31                           # ~3.1 us
    assert round(float(alone["p_wait_10us"]), 4) == 0.0045 and round(float(alone["p_wait_100us"]), 4) == 0.0015
    assert float(alone["p_wait_10us"]) < 0.01 and float(alone["p_wait_100us"]) > 0.001   # p99 < 10 us < 100 us < p99.9
    assert round(float(shared["stolen_fraction"]), 2) == 0.51
    assert round(float(shared["p_wait_10us"]), 3) == 0.502 and round(float(shared["p_wait_100us"]), 3) == 0.490
    # named result: some six thousand times less time stolen, some 2,700 times shorter worst gap on the tuned model
    assert round(float(alone["stolen_fraction"]) / 2e-6, -3) == 7_000 or 6_000 <= float(alone["stolen_fraction"]) / 2e-6 < 7_000
    assert round(float(alone["worst_ns"]) / 2000, -2) == 2_700


def test_measured_curve():
    c = rows("measured_hiccups.csv", "threshold_ns")
    assert round(float(c["5000"]["alone"]), -1) == 750                             # some 750 a second >= 5 us
    assert 1 < float(c["100000"]["alone"]) < 10                                    # a few a second > 100 us
    assert 0 < float(c["1000000"]["alone"]) <= 0.5                                  # every few seconds >= 1 ms
    sh = c["2000000"]["shared"]
    assert 80 < float(sh) < 160 and float(c["5000000"]["shared"]) < 0.1 * float(sh)   # ~120 a second of ~4 ms


def test_measured_receive_and_lock():
    r = rows("measured_receive.csv", "key")
    block, spin = float(r["udp-block"]["p50"]), float(r["udp-spin"]["p50"])
    assert 15_000 < block < 60_000 and 1_500 < spin < 4_000 and block / spin > 10    # ~30 us vs ~2.3 us
    assert 800 < float(r["pipe-same"]["p50"]) < 2_500                                # ~1.5 us: two switches
    assert 15_000 < float(r["pipe-two"]["p50"]) < 60_000                             # ~30 us: waking an idle CPU
    assert float(r["udp-spin"]["p999"]) > 10_000                                    # tails still tens of us
    m = rows("measured_mlock.csv", "case")
    assert int(m["unlocked"]["faults"]) == 8192 and int(m["locked"]["faults"]) == 0
    assert 700 < float(m["unlocked"]["touch_ns_per_page"]) < 3000 and 15 < float(m["locked"]["touch_ns_per_page"]) < 80
    p = rows("measured_privileges.csv", "request")
    assert p["SCHED_FIFO"]["result"] == "EPERM"


def test_measured_audit():
    a = rows("measured_audit.csv", "rule")
    assert len(a) == 11
    fails = {k for k, v in a.items() if v["status"] == "fail"}
    assert fails == {"isolated", "siblings", "nohz_full", "rcu_nocbs", "irq_affinity", "cstate", "memlock"}
    assert sum(v["status"] == "ok" for v in a.values()) == 3 and a["governor"]["status"] == "unknown"
