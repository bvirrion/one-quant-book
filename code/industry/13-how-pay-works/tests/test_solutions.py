"""Numbers gate: every numerical answer printed in Book 17, chapter 13 (text and solutions)."""
import dataclasses
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import in_pay as a  # noqa: E402

po = a.po


def k(x):
    return round(float(x) / 1000)


def test_nyc_bonus_arithmetic():
    assert round(100 * (180_000 / 257_500 - 1), 1) == -30.1 and round(100 * (244_700 / 176_500 - 1), 1) == 38.6


def test_uk_deferral_and_discount():
    d = 0.4 * 660_000 + 0.6 * (1_000_000 - 660_000)
    assert d == 468_000 and round(1.05 ** -4, 2) == 0.82
    assert round(0.85 * 100_000) == 85_000


def test_offers_table():
    t = a.table()
    assert [k(t[n]["mean"]) for n in ("bank", "market maker", "platform analyst")] == [1618, 1949, 1703]
    assert [k(t[n]["p10"]) for n in ("bank", "market maker", "platform analyst")] == [597, 686, 171]
    assert [k(t[n]["p90"]) for n in ("bank", "market maker", "platform analyst")] == [2230, 2956, 3010]
    assert [k(t[n]["ce1"]) for n in ("bank", "market maker", "platform analyst")] == [1500, 1779, 1439]
    assert [k(t[n]["ce3"]) for n in ("bank", "market maker", "platform analyst")] == [1186, 1365, 904]
    assert round(t["platform analyst"]["ce1"], -3) == 1_439_000 and round(t["bank"]["ce1"], -3) == 1_500_000
    assert round(100 * a.platform_cut_share(), 1) == 35.4


def test_handcuff_and_buyout():
    assert [round(x, -3) for x in a.bank_unvested()] == [90_000, 158_000, 203_000, 226_000, 226_000]
    fo = a.forfeit_by_year()
    assert round(fo[1], -3) == 129_000 and round(fo[3], -3) == 170_000
    assert round(a.buyout_year2(), -3) == 158_000
    assert round(0.4 * 200_000 * np.exp(0.125) / 4) == 22_663 and round(7 * 0.4 * 200_000 * np.exp(0.125) / 4) == 158_641


def test_good_leaver():
    g = dataclasses.replace(a.BANK, name="bank gl", good_leaver=True)
    s = po.simulate(g, a.YEARS, a.HAZARD, a.RATE, a.N, np.random.default_rng(a.SEED))
    b = a.sims()["bank"]
    assert round(b["forfeited"].mean()) == 55_022 and s["forfeited"].mean() == 0.0
    assert round(b["pv"].mean()) == 1_617_971 and round(s["pv"].mean()) == 1_672_994


def test_iq_ce():
    assert round(po.certainty_equivalent(np.array([0.0, 200.0]), 1.0, 100.0), 1) == 73.2


def test_small_runs():
    s = po.simulate(a.PLATFORM, 3, 0.1, 0.05, 2000, np.random.default_rng(1))
    sm = po.summary(s)
    assert sm["p10"] < sm["p50"] < sm["p90"] and 0 < s["cut"].mean() < 1
