"""Numbers gate: every numerical answer printed in Book 2, Chapter 18 (text and solutions)."""
import datetime as dt
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/ndf"))
from firm_ndf import band, fixing_date
from ndf_demo import cny_cnh, krw_ndf, load_eurchf, unpeg

R = dict(load_eurchf())
U = unpeg()
C = cny_cnh()
K = krw_ndf()


def test_text():
    assert (R["2011-09-05"], R["2011-09-06"], R["2015-01-14"], R["2015-01-15"], R["2015-01-23"]) == (
        1.1111, 1.2036, 1.201, 1.028, 0.9816)
    assert round(U["move"] * 100, 1) == 14.4 and U["low_month"] == 0.9816
    assert (round(C["onshore"] * 100, 2), round(C["offshore"] * 100, 2), round(C["basis"] * 100, 2)) == (0.31, 0.89, 0.58)
    assert (round(C["band_lo"], 4), round(C["band_hi"], 4)) == (6.9580, 7.2420)
    assert round(K["settlement"]) == 319_186 and round(-K["if_1350"]) == 222_222
    assert dt.date.fromordinal(int(K["fixing_day"])) == dt.date(2026, 10, 9)
    assert [round(U["by_leverage"][k], 2) for k in (20, 50)] == [2.88, 7.2]


def test_exercises():
    assert round(-K["seller"]) == 319_186
    assert band(7.10, 0.02) == (7.10 * 0.98, 7.10 * 1.02)
    assert fixing_date(dt.date(2026, 10, 5), {dt.date(2026, 10, 2)}) == dt.date(2026, 9, 30)
    during = {d: v for d, v in R.items() if "2011-09-07" <= d <= "2015-01-14"}
    lo = min(during, key=during.get)
    assert (lo, during[lo]) == ("2012-06-01", 1.2008)


def test_problem():
    assert round(U["margin"]) == 60_050 and round(1e6 * (1.2010 - 1.19)) == 11_000
    assert round(U["loss"]) == 173_000 and round(U["multiple"], 2) == 2.88 and round(U["negative_balance"]) == 112_950
    assert round(U["before"] - U["after"], 2) == 0.17
