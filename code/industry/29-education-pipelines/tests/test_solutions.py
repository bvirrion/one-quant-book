"""Numbers gate: every numerical answer printed in Book 17, chapter 29 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import in_edu as a  # noqa: E402

fe = a.fe


def r(x, d=1):
    return round(float(x), d)


def test_completions():
    c = a.completions()
    assert [c[(y, "financial mathematics", "master")] for y in (2010, 2014, 2019, 2024)] == [305, 773, 3554, 4584]
    want = {"financial mathematics": (611, 4584, 24), "financial analytics": (553, 870, 4),
            "statistics": (3379, 2716, 454), "mathematics": (14333, 2230, 1165),
            "computer science": (44627, 25543, 1628), "physics": (6008, 1934, 1760)}
    got = {f: tuple(c[(2024, f, lv)] for lv in ("bachelor", "master", "doctorate (research)")) for f in want}
    assert got == want
    assert r(4584 / 305) == 15.0 and 4584 / 25543 < 0.2
    assert sum(want[f][2] for f in ("physics", "computer science", "mathematics", "statistics")) == 5007
    assert (r(25543 / 11598, 2), r(4584 / 3554, 2)) == (2.20, 1.29)


def test_reports_and_ratio():
    b, m = a.reports()
    assert (b.seeking, b.accepted, b.median_base, b.reporting) == (70, 67, 150_000, None)
    assert r(100 * b.placement_rate) == 95.7 and b.median_quantile_bounds() is None
    lo, hi = m.median_quantile_bounds()
    assert (m.seeking, m.accepted, m.reporting, m.median_base) == (98, 98, 89, 145_000)
    assert (r(100 * lo), r(100 * hi)) == (44.9, 55.1)
    x = fe.PlacementReport("x", "x", 98, 98, 98, 60, 1.0, "")
    assert tuple(r(100 * v) for v in x.median_quantile_bounds()) == (18.3, 81.7)
    masters, filings, ratio = a.named()
    assert (masters, filings, round(ratio, 2)) == (5454, 1466, 3.72)


def test_small_runs():
    assert "master" in fe.LEVELS.values()
