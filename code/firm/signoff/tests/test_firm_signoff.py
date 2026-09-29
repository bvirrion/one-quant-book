import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_signoff as so  # noqa: E402


def test_walk_on_hand_numbers():
    sod, sod_px = {"A": 100, "B": -50}, {"A": 1000, "B": 2000}
    fills = [(10, "A", 1, 10, 1010, 5), (20, "B", 1, 50, 1990, 7)]      # the second fill misses the cut at 15
    flash, close, final = {"A": 1020, "B": 1980}, {"A": 1030, "B": 1985}, {"A": 1025, "B": 1985}
    w = so.walk(sod, sod_px, fills, 15, flash, close, final)
    assert w["flash"] == 110 * 20 - 10 * 10 + 50 * 20                  # A: +2,100; B short gains 1,000
    assert w["market moves after the flash"] == 110 * 10 - 50 * 5
    assert w["late trades"] == 50 * (1985 - 1990) and w["fees"] == -12
    assert w["valuation adjustments"] == 110 * (1025 - 1030) and w["unexplained"] == 0
    assert w["final"] == w["flash"] + sum(v for k, v in w.items() if k not in ("flash", "final", "unexplained"))


def test_verified_marks_and_exceptions():
    v = so.verified_marks({"X": 1000, "Y": 500}, {"X": 950}, {"X": 20})
    assert v == {"X": 970, "Y": 500}
    w = {"flash": 1000.0, "final": 850.0, "late trades": 0.0, "valuation adjustments": -150.0, "unexplained": 0}
    assert so.exceptions(w, 100.0, 0.10, {"valuation adjustments": 100.0}) == [("flash to final", -150.0),
                                                                               ("valuation adjustments", -150.0)]
    t = so.Trail()
    assert so.sign(t, "pc", "19:00", w, []) == "signed" and so.sign(t, "pc", "19:05", w, [("x", 1)]) == "escalated"
    assert [e[0] for e in t.entries] == [1, 2]


def test_tax():
    assert abs(so.tax_drag(0.08, 10, 0.002, 0.02, 0.15) - (0.08 - 0.02 - 0.003)) < 1e-12
    assert so.half_turnover(0.08, 0.002) == 20.0 and abs(so.blended(0.37, 0.20) - 0.268) < 1e-12
