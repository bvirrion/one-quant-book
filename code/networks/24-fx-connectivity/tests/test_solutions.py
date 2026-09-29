"""Numbers gate: every number printed in Book 14, chapter 24 (text and solutions)."""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "python"))
import nw_fx as n  # noqa: E402

fx, S = n.fx, n.SITES


def test_floors_table():
    f = {s: fx.one_way_ms("ld4", s, 1.0, S) for s in ("ny5", "ny6", "ty3", "sg1")}
    assert [round(f[s], 2) for s in ("ny5", "ny6", "ty3", "sg1")] == [27.07, 27.07, 46.85, 53.10]
    assert [round(1.5 * f[s], 1) for s in ("ny5", "ty3", "sg1")] == [40.6, 70.3, 79.7]
    assert [round(3 * f[s], 1) for s in ("ny5", "ty3", "sg1")] == [81.2, 140.5, 159.3]
    o = n.order_paths()
    assert (round(o["ny5"], 1), round(o["ld4"], 1), round(1000 * sum(n.STAGES.values()))) == (79.5, 70.3, 40)


def test_staleness_and_holds():
    t = n.staleness_table()
    assert {round(t[("ld4", v)], 1) for v in n.VENUE_SITES} == {0.1}
    assert [round(t[("ty3", v)], 1) for v in n.VENUE_SITES] == [0.1, 31.5, 31.5, 140.6, 111.1]
    assert [round(t[("ny5", v)], 1) for v in n.VENUE_SITES] == [0.1, 81.3, 81.3, 31.5, 8.2]
    k = n.tokyo()
    assert (round(k["stale_equal"], 1), round(k["stale_backbone"], 1)) == (140.6, 185.6)
    assert (round(k["hold_equal"], 1), round(k["hold_backbone"], 1)) == (0.1, 45.1)
    assert round(k["stale_equal"]) == 141


def test_caught_and_aggregator():
    c = n.caught_curves()
    assert (round(100 * c["equal"][0]), round(100 * c["equal"][2], 1)) == (70, 99.4)
    b = dict(zip(n.HOLDS, c["backbone"], strict=True))
    assert (round(100 * b[47], 1), round(100 * b[46], 1)) == (99.4, 96.2)
    assert min(h for h in n.HOLDS if b[h] >= 0.99) == 47
    w = n.aggregator_windows()
    assert (round(w["ld4"], 1), round(w["ny6"], 1), w["ty3"]) == (140.5, 158.9, 0.0)


def test_small_runs():
    assert fx.hold_ms("ty3", "ld4", "ty3", fx.Paths(info=1.0, proc_ms=0.0), S) == 0.0
    assert len(fx.caught("ny5", "ld4", "ny5", n.EQUAL, [0, 5], n=200, table=S)) == 2
