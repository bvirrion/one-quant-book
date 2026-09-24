"""Numbers gate: every numerical answer printed in the Chapter 18 text and solutions."""
import csv
import datetime as dt
import pathlib
import sys
from fractions import Fraction as Fr

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/contracts"))
from firm_contracts import parse_thirty_seconds, third_friday
from futures_basics import SPECS, hedge, leverage

S = {s.root: s for s in SPECS}
CSV = pathlib.Path(__file__).resolve().parents[4] / "figdata/markets-1/18-futures-contracts-and-exchanges/residual.csv"


def test_text():
    assert S["ES"].notional == 300_000 and S["ES"].tick_value == 12.5
    assert parse_thirty_seconds("112-165") == 112 + Fr(33, 64) and 100_000 / 64 / 100 == 15.625
    assert S["FESX"].tick_bp / S["ES"].tick_bp > 4
    assert 0.02 / 0.05 == pytest.approx(0.40) and 150_000 * 2 == S["ES"].notional


def test_exercises():
    ticks = (Fr("6012.50") - Fr("5987.25")) / Fr("0.25")
    assert ticks == 101 and 101 * 12.5 * 12 == 15_150
    a, b = parse_thirty_seconds("111-245"), parse_thirty_seconds("112-080")
    assert (float(a), float(b), (b - a) * 64) == (111.765625, 112.25, 31) and 31 * 15.625 == 484.375
    assert third_friday(2027, 3) == dt.date(2027, 3, 19)
    assert round(leverage(S["ES"], 21_000), 1) == 14.3 and 21_000 / 300_000 == pytest.approx(0.07)
    assert round(50e6 / 54_000) == 926 and round(926 * 10 / 2) == 4_630
    pos, oi, vol = {k: 0 for k in "ABCD"}, [], 0
    for buyer, seller, q in (("A", "B", 5), ("C", "A", 3), ("B", "C", 2), ("D", "A", 4)):
        pos[buyer] += q
        pos[seller] -= q
        vol += q
        oi.append(sum(v for v in pos.values() if v > 0))
    assert oi == [5, 5, 3, 5] and pos == {"A": -2, "B": -3, "C": 1, "D": 4} and vol == 14
    with open(CSV) as f:
        rows = [r for r in csv.DictReader(f) if float(r["portfolio_m"]) >= 1.0]
    assert max(float(r["residual_pct_es"]) for r in rows) == 14.29
    assert max(float(r["residual_pct_micro"]) for r in rows) == 1.0


def test_problem():
    assert S["ES"].notional == 300_000 and S["FESX"].notional == 54_000
    assert round(1.15 * 187e6 / 300e3, 2) == 716.83 and hedge(187e6, 1.15, S["ES"])[0] == 717
    assert hedge(187e6, 1.15, S["ES"])[1] == pytest.approx(-50_000)
    assert round(0.9 * 43e6 / 54e3, 2) == 716.67 and hedge(43e6, 0.9, S["FESX"]) == (717, pytest.approx(-18_000))
    assert third_friday(2026, 12) == dt.date(2026, 12, 18) and dt.date(2026, 12, 18) == dt.date(2026, 9, 18) + dt.timedelta(days=91)
    assert 717 * 300e3 * 0.05 == pytest.approx(10_755_000)
    assert 717 * 300e3 * 0.02 == pytest.approx(4_302_000) and 1.15 * 0.02 * 187e6 == pytest.approx(4_301_000)
    assert 4_302_000 - 0.029 * 187e6 == pytest.approx(-1_121_000)
    assert 0.10 * 187e6 == pytest.approx(18.7e6) and 18.7e6 / 50_000 == pytest.approx(374)
    assert 717 * 2.5 == 1792.5
