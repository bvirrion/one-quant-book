"""Numbers gate, Book 13 chapter 16."""
import csv
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE / "python"))
import ll_lines as L  # noqa: E402

FIG = ROOT / "figdata/low-latency/16-protocols-ii-binary-exchange-protocols"


def rows(name):
    with open(FIG / name, newline="", encoding="utf8") as f:
        return list(csv.DictReader(f))


def test_simulated_lines_reproduce_the_figure(tmp_path):
    L.record(60, tmp_path)                                     # deterministic: the figure's run
    a, b = L.packets(tmp_path / "lineA.bin"), L.packets(tmp_path / "lineB.bin")
    arb = L.arbitrate(a, b)
    assert arb[2] == 2 and arb[3] == 18                        # the overlap: 17 messages, and 1 more
    assert L.line_gaps(a)[2] > 5 and L.line_gaps(b)[2] > 5
    s = {r["stream"]: r for r in rows("gaps_summary.csv")}
    assert (s["A"]["gaps"], s["A"]["missing"], s["B"]["gaps"], s["B"]["missing"]) == ("56", "160", "65", "186")
    assert (s["arbitrated"]["gaps"], s["arbitrated"]["missing"]) == ("2", "18")
    assert 31_000 < int(s["arbitrated"]["messages"]) < 33_000 and 31_000 < int(s["A"]["packets"]) < 33_000
    ev = [(float(r["t_s"]), int(r["missing"])) for r in rows("gaps_events_arb.csv")]
    assert [m for _, m in ev] == [1, 17] and all(10.0 < t < 10.1 for t, _ in ev)


def test_exercises_and_problem():
    assert 0x000F42A4 == 1_000_100                                                     # exercise 2
    assert abs(L.both_lost_independent(0.002) - 4e-6) < 1e-18                          # exercise 3
    assert round(L.both_lost_common(0.002, 1e-4), 8) == 1.04e-4
    g = L.ge_stationary_loss(0.0005, 0.1, 0.8)
    assert round(0.0005 / 0.1005, 4) == 0.005 and round(g, 4) == 0.004 and 1 / 0.1 == 10  # exercise 4
    assert 37 + 8 == 45                                                                 # exercise 6
    n = 50_000 * 23_400
    assert n == 1_170_000_000 and round(n * 1e-4) == 117_000
    assert round(L.both_lost_independent(1e-4) * n, 1) == 11.7
    assert round(L.both_lost_common(1e-4, 1e-6) * n) == 1182 and round(L.both_lost_common(1e-4, 1e-6), 8) == 1.01e-6
    assert round(g * g, 6) == 1.6e-5
    assert L.snapshot_recovery_s(1, 0.02) == 0.52 and L.snapshot_recovery_s(1, 0.02, worst=True) == 1.02
    assert round(26_000 * 8e-9 * 1e3, 2) == 0.21 and round(51_000 * 8e-9 * 1e3, 2) == 0.41


def test_measured():
    d = {r["key"]: float(r["ns_per_msg"]) for r in rows("measured_decode.csv")}
    assert 6 < d["book1"] < 25 and 2.5 < d["flyweight"] < 10 and 2.5 < d["sbe"] < 10
    assert d["book1"] / d["flyweight"] > 1.5                                           # the copy and the call: half
    assert abs(d["sbe"] / d["flyweight"] - 1) < 0.25                                   # byte order: nothing measurable
    assert round(d["book1"]) == 11 and round(d["flyweight"]) == 5 and round(d["sbe"]) == 5
    assert 4 < d["packets"] < 8 and round(d["packets"]) == 7 and 5 < d["rust"] < 20 and round(d["rust"]) == 8
    assert d["packets"] * 1e6 / 1e9 < 0.01                                             # under 1% of a core at 1M/s
    arb = rows("measured_arb.csv")[0]
    assert (arb["gaps"], arb["missing"]) == ("2", "18") and 0.5 < float(arb["ns_per_packet"]) < 8
    assert round(float(arb["ns_per_packet"]), 1) == 1.3
