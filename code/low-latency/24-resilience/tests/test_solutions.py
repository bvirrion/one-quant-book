"""Numbers gate, Book 13 chapter 24."""
import csv
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
ROOT = HERE.parents[2]
FIG = ROOT / "figdata/low-latency/24-resilience"
sys.path.insert(0, str(HERE / "python"))
import ll_failover as L  # noqa: E402

sq, sim = L.sq, L.sim


def rows(name):
    with open(FIG / name, newline="", encoding="utf8") as f:
        return list(csv.DictReader(f))


def test_exercises():
    j = sq.Journal()
    j.append(1, "M", 1)
    j.fence(3)
    try:
        j.append(2, "M", 2)
        refused = False
    except ValueError:
        refused = True
    assert refused
    assert sq.cl_for((46, 0)) == 736
    assert round(L.p_duplicate(500, 40_000, 0.9) * 100, 1) == 1.8
    assert round(37e6 * 37e-9, 1) == 1.4 and round(37e6 / 6.5 * 37e-9, 1) == 0.2


def test_table_and_problem():
    t = {(r["procedure"], r["stage"]): int(r["duplicates"]) for r in rows("failover.csv")}
    assert t[("fresh ids", "sent; in flight")] == 27 and t[("fresh ids", "at the venue; not yet reported")] == 27
    assert sum(v for (p, _), v in t.items() if p != "fresh ids") == 0
    s = {r["procedure"]: r for r in rows("failover_summary.csv")}
    assert (int(s["fresh ids"]["points"]), int(s["fresh ids"]["duplicates"])) == (184, 54)
    assert int(s["fresh ids"]["max_position"]) == 1_100 and int(s["idempotency keys"]["max_position"]) == 1_000
    for r in s.values():
        assert round(float(r["recovery_min_ms"]), 1) == 2.8 and round(float(r["recovery_max_ms"]), 1) == 3.1
    rate = 46 / 0.060
    assert round(rate) == 767 and L.duplicate_window_ns() == 40_000
    assert round(27 * 40e-6 / 0.060 * 100, 1) == 1.8
    assert round(L.p_duplicate(5_000, fill_fraction=27 / 46) * 100, 1) == 11.7
    free = sim.run(None)
    assert free.orders == 46 and free.position == -700 and 46 - 27 == 19


def test_measured_apply():
    r = rows("measured_apply.csv")[0]
    ns = float(r["ns_per_entry"])
    assert 25 <= ns <= 50 and round(ns) in range(33, 42)
    assert 1.0 <= 37e6 * ns * 1e-9 <= 1.9                 # "about a second and a half"
