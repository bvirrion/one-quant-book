"""Numbers gate: every numerical answer printed in Book 10, chapter 21 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from mx_xexec import BOND, MARKETS, NOTIONAL, bonds, crypto, futures, fx, table  # noqa: E402


def r(x, d=1):
    return round(float(x), d)


def test_futures_and_fx():
    f = futures()
    assert (f["points"]["legs"], f["points"]["spread_book"], f["points"]["mid"]) == (0.4375, 0.225, -10.25)
    assert (r(f["legs"], 3), r(f["spread_book"], 2), f["implied"] == f["spread_book"]) == (0.875, 0.45, True)
    assert 200 * 5000 * 50 == NOTIONAL
    x = fx()
    assert (r(100 * x["reject_rate"]), r(x["aggregator"], 3), r(x["last_look"], 3), x["firm_only"]) == (7.7, 0.087, 0.007, 0.15)
    assert r(x["child"] / 1e6) == 2.5


def test_bonds_crypto_and_table():
    b = bonds()
    assert b["best_n"] == 3
    assert [r(b["by_n"][n]["total"], 2) for n in (1, 2, 3, 4)] == [49.27, 46.26, 45.50, 45.54]
    assert (r(b["best"]["competition"], 2), r(b["best"]["leakage"]), r(BOND["markup"] - 5.0)) == (-6.77, 3.0, 44.3)
    assert r(b["by_n"][3]["competition"] - b["by_n"][4]["competition"], 2) == 1.46
    c = crypto()
    assert (c["x"], r(c["saving"], 2), c["schedule_ok"], c["burst_ok"]) == (1_375_000.0, 0.36, True, False)
    t = table()
    assert [r(t[k]["total"], 2) for k in ("futures", "fx", "bond", "crypto")] == [1.81, 0.54, 45.50, 21.14]
    assert [r(100 * t[k]["rule_share"]) for k in ("futures", "fx", "bond", "crypto")] == [24.9, 1.3, -8.3, -1.7]
    assert (r(t["futures"]["impact"], 2), r(t["fx"]["impact"], 2), r(t["bond"]["impact"], 2), r(t["crypto"]["impact"], 2)) == (
        1.11, 0.45, 49.27, 21.0)
    assert (r(100 * NOTIONAL / MARKETS["futures"].adv, 3), r(100 * NOTIONAL / MARKETS["bond"].adv)) == (0.025, 250.0)


def test_exercise_7():
    from firm_xexec import rfq
    tot = {n: rfq(n, BOND["markup"], 8.0, 3.0)["total"] for n in range(1, 11)}
    best = min(tot, key=tot.get)
    assert (best, r(tot[best], 2)) == (2, 47.76)
    assert r(0.7 * 40 * math.sqrt(2.5)) == 44.3
