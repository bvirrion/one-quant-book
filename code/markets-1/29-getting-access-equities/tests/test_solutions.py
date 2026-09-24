"""Numbers gate: every numerical answer printed in the Chapter 29 text and solutions."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from access_costs import MAKER_TAKER, TCV, cost_table, monthly_rebate

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/feesched"))
from firm_feesched import breakeven_natural_volume, extra_volume_worth_adding


def test_text():
    assert monthly_rebate(24.0e6) - monthly_rebate(23.9e6) == pytest.approx(155_400)
    t = {n.split()[0]: (round(p * 1e4), round(a * 1e4)) for n, p, a in cost_table(9e6)}
    assert t == {"maker-taker": (-17, 33), "inverted": (13, -3), "flat-fee": (6, 6)}
    assert 0.0010 - (-0.0020) == pytest.approx(0.0030)           # 'three tenths of a cent' between the two passive rates


def test_exercises():
    assert 9e6 / TCV == pytest.approx(0.00075) and MAKER_TAKER.add_rate(9e6, TCV) == -0.0020
    assert 9e6 * 0.0020 == pytest.approx(18_000) and monthly_rebate(9e6) == pytest.approx(378_000)
    assert -MAKER_TAKER.daily_bill(23.9e6, 0, TCV) == pytest.approx(47_800)
    assert -MAKER_TAKER.daily_bill(24.0e6, 0, TCV) == pytest.approx(55_200)
    assert -17 + 33 == 16
    assert max(100_000, min(300 * 2_500, 1_000_000)) == 750_000 and 15 * 2_000_000 == 30_000_000
    assert 0.10 * 390 == 39
    assert breakeven_natural_volume(0.0020, 0.0023, 24e6, 0.0027) == pytest.approx(24e6 * 4 / 7)
    assert round(24e6 * 4 / 7 / 1e6, 1) == 13.7
    assert breakeven_natural_volume(0.0020, 0.0023, 24e6, 0.0025) == pytest.approx(9.6e6)
    assert 0.01 * TCV == 120e6 and 2e6 / TCV < 0.0006
    assert round(2e6 * (0.0010 + 0.0016 - 0.0003) * 21) == 96_600 and round(2e6 * 0.0041 * 21) == 172_200


def test_problem():
    assert MAKER_TAKER.add_rate(20e6, TCV) == -0.0020 and monthly_rebate(20e6) == pytest.approx(840_000)
    extra, gain = extra_volume_worth_adding(MAKER_TAKER, 20e6, TCV, 0.0027)
    assert extra == pytest.approx(4e6) and gain == pytest.approx(4_400)
    extra3, gain3 = extra_volume_worth_adding(MAKER_TAKER, 24e6, TCV, 0.0027)
    assert extra3 == pytest.approx(6e6) and gain3 == pytest.approx(12_600)
    assert breakeven_natural_volume(0.0023, 0.0028, 30e6, 0.0027) == 0.0
    client = 0.8 * 0.0028
    assert client == pytest.approx(0.00224)
    assert client * 20e6 * 21 == pytest.approx(940_800) and 840_000 - 25_000 == 815_000
    assert 0.0028 * 30e6 * 21 - 25_000 == pytest.approx(1_739_000) and client * 30e6 * 21 == pytest.approx(1_411_200)
    assert (24 * 21 - 23 * 15) / 6 == 26.5 and 0.0020 * 13e9 == 26e6
    assert round((0.0031 - 0.0020) * 1e4) == 11
