"""Numbers gate: every numerical answer printed in Book 9, chapter 18 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s2_creditrv import at_the_trough, basis_book, basis_stats, rv_trades  # noqa: E402


def r(x, d=1):
    return round(float(x), d)


def pct(x, d=1):
    return round(100 * float(x), d)


def test_basis():
    b = basis_stats()
    assert (r(b["normal"]), r(b["trough"]), r(b["trough_year"], 2), r(b["cds_mean"], 0)) == (-14.9, -150.7, 5.25, 136.0)


def test_books():
    got = {f: tuple(pct(basis_book(f)[k]) for k in ("before", "to_low", "recovery", "ten_years")) for f in (0.0, 30.0, 60.0)}
    assert got == {0.0: (1.6, -59.9, 76.0, 24.4), 30.0: (-1.1, -60.6, 63.2, -2.6), 60.0: (-3.8, -61.2, 50.4, -29.6)}
    assert r(basis_book(0.0)["sr_before"], 2) == 0.76
    t = {f: tuple(pct(at_the_trough(f)[k]) for k in ("total", "carry", "marks")) for f in (0.0, 30.0)}
    assert t == {0.0: (69.8, 8.4, 61.4), 30.0: (67.1, 5.7, 61.4)}


def test_rv_trades():
    x = rv_trades()
    assert {k: (r(v["bp"], 0), round(v["sr"], 2), pct(v["active"], 0)) for k, v in x.items()} == {
        "index": (55.0, 0.97, 60.0), "curve": (49.0, 0.75, 62.0)}


def test_exercises():
    assert (round(10 * (15 - 0.9 * 30) / 100, 2), round(4.5 * 135 / 100 * 10, 1), round(1 / 0.10)) == (-1.2, 60.8, 10)


def test_stop_out():
    from s2_creditrv import stop_out
    s = stop_out()
    assert (pct(s["locked"]), round(s["year"], 2), pct(s["held"])) == (-50.5, 5.24, 24.4)
