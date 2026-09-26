"""Numbers gate: every numerical answer printed in Book 11, chapter 12 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import hf_etf as h  # noqa: E402

fe = h.fe


def r(x, d=0):
    return round(float(x), d)


def test_errors():
    e = h.errors()
    assert (r(e["normal"]["nav_bp"], 1), r(e["freeze"]["nav_bp"]), r(e["normal"]["basket_bp"], 1),
            r(e["freeze"]["basket_bp"], 1)) == (13.7, 214, 3.5, 9.9)
    assert (r(e["normal"]["age_min"] / 60), r(e["freeze"]["age_min"] / 60)) == (2, 11)


def test_table():
    t = h.table()
    got = [(r(v["normal"], -2), r(v["sd"], -2), r(v["freeze"] / 1e6, 2)) for v in t.values()]
    assert got == [(132100, 24300, -70.61), (111600, 16000, -69.91), (163600, 13500, 3.17), (149100, 9300, 3.55),
                   (148300, 9400, 3.26)]
    nav = t["NAV, unhedged"]
    assert r(100 * nav["freeze_spread"] / nav["freeze"]) == 95
    assert r(t["basket, hedged, redeem"]["freeze_flatten"], -3) == -262000
    assert r(t["basket, unhedged"]["normal"] - t["basket, hedged"]["normal"], -2) == 14500
    assert r(100 * (t["basket, unhedged"]["normal"] / nav["normal"] - 1)) == 24
    assert r(nav["freeze"] / nav["normal"], -1) == -530


def test_decomposition():
    d = h.decomposition()
    assert (d["day"], r(d["premium"]), r(d["stale"]), r(d["pressure"])) == (42, -532, 557, -5)


def test_sparser():
    a, b = h.sparser(10.0), h.sparser(100.0)
    assert (r(a["max_stale"]), r(b["max_stale"]), r(a["basket_bp"], 1), r(b["basket_bp"], 1)) == (557, 722, 13.8, 16.5)
    assert (r(a["basket"] / 1e6, 2), r(b["basket"] / 1e6, 2), r(a["nav"] / 1e6, 1), r(b["nav"] / 1e6, 1)) == (
        3.43, 3.48, -84.7, -96.9)


def test_exercises():
    assert r(h.unit_fee_bp(), 2) == 0.86
    assert r(fe.closed_fair(100.0, 1.0, 0.015, -0.005), 2) == 100.99
    act, edge = fe.creation_decision(100.05, 100.0, 50000, 1250.0, 2.0)
    assert act == "create" and r(edge) == 250
