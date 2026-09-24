"""Tutorial of Book 2, Chapter 7: the printed end state is reproduced."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from sovereign_demo import euro_spreads, exhaustion_bp, fund, latest, nav_curve, widening_2011, yields


def test_widening_2011():
    w = widening_2011()
    assert (round(w["change"]), round(w["italy"]), round(w["germany"])) == (326, 224, 102)


def test_spreads_and_latest():
    sp = euro_spreads()
    peak = max(sp["IT"], key=lambda t: t[1])
    assert peak[0] == "2011-11-01" and round(peak[1]) == 518
    es = max(sp["ES"], key=lambda t: t[1])
    assert es[0] == "2012-07-01" and round(es[1]) == 555
    assert (round(sp["IT"][-1][1]), round(sp["FR"][-1][1]), round(sp["ES"][-1][1])) == (81, 82, 45)
    y = latest()
    assert (y["DE"], y["JP"], round(y["GB"], 2)) == (3.18, 2.94, 4.99)
    assert yields()["JP"][-1][0] == "2026-08-01"


def test_ldi_curve():
    c = dict(nav_curve())
    assert c[0] == 100.0 and round(c[160]) == 43
    assert round(exhaustion_bp()) == 351 and fund(360)["cushion"] < 0 < fund(340)["cushion"]
