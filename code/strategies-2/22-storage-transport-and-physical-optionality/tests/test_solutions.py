"""Numbers gate: every numerical answer printed in Book 9, chapter 22 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s2_physopt import UNIT, cargo, gated, hedging, henry_hub, storage, transport_strip  # noqa: E402


def r(x, d=1):
    return round(float(x), d)


def test_storage():
    s = storage()
    assert s["plan"] == [2, 2, 2, 2, 2, 0, 0, 0, -4, -4, -2, 0] and s["pairs_n"] == 10
    assert [r(s[k] * UNIT / 1000, 0) for k in ("intrinsic", "pairs", "lsm", "rolling")] == [716, 722, 760, 773]
    by_hand = (4 * 3.45 + 4 * 3.50 + 2 * 3.30 - 2 * (2.60 + 2.62 + 2.68 + 2.74 + 2.78) - 20 * 0.02) * UNIT
    assert r(by_hand, 0) == 716000.0                                                     # exercise 1


def test_hedging():
    h = hedging()
    assert h["static_sd"] < 1e-9 and h["static_units"] == 20
    got = [(r(h[c]["mean"] * UNIT / 1000), r(100 * h[c]["below"]), r(h[c]["extra_units"])) for c in (0.0, 0.005, 0.02)]
    assert got == [(56.8, 0.0, 15.1), (49.2, 3.1, 15.1), (26.6, 32.6, 15.1)]
    g = gated(0.02)
    assert (r(g["mean"] * UNIT / 1000), r(100 * g["below"]), r(g["extra_units"])) == (37.4, 0.0, 9.2)
    g = gated(0.005)                                                                      # exercise 7
    assert (r(g["mean"] * UNIT / 1000), r(100 * g["below"]), r(g["extra_units"])) == (50.1, 0.0, 13.0)


def test_transport_and_cargo():
    assert [r(transport_strip(rho=x)[k] * UNIT / 1000, 0) for x, k in ((0.85, "intrinsic"), (0.85, "option"), (0.5, "option"),
                                                                        (0.95, "option"))] == [139, 369, 580, 273]
    assert (r(0.60 - 0.10, 2) * UNIT, r(cargo()["switch"], 2), r(cargo(0.5)["switch"], 2)) == (50000.0, 0.64, 1.08)
    assert (max(10.5 - 10.0 - 0.8, 0.0), r(11.2 - 10.0 - 0.8, 2)) == (0.0, 0.4)


def test_henry_hub():
    h = henry_hub()
    assert (h["first"], h["last"], h["years"], h["positive"], r(h["mean"], 2), r(h["sd"], 2), r(h["median"], 2)) == (
        2007, 2025, 19, 12, -0.07, 2.04, 0.36)
    assert (h["worst_year"], r(h["worst"], 2), h["best_year"], r(h["best"], 2)) == (2008, -6.12, 2025, 1.98)
    import csv
    with open(pathlib.Path(__file__).resolve().parents[4] / "data/strategies-2/hh_years.csv") as fh:
        years = {int(x["year"]): float(x["spread"]) for x in csv.DictReader(fh)}
    assert r(years[2022], 2) == -3.71
