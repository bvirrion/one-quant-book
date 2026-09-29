"""Numbers gate: every numerical answer printed in Book 17, chapter 5 (text and solutions)."""
import csv
import math
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import in_platforms as p  # noqa: E402

tt = p.tt
FIG = pathlib.Path(__file__).resolve().parents[4] / "figdata/industry/05-multi-manager-platforms/survival.csv"


def r(x, d=1):
    return round(float(x), d)


def test_panel_and_growth():
    g = p.growth("Millennium Management", "2016-01", "2026-01")
    assert (r(g["employees"], 2), r(g["raum"], 2), r(100 * (g["raum_per_employee"] - 1), 0)) == (3.78, 3.15, -17)
    assert [r(100 * x, 0) for x in g["advisory_share"]] == [63, 47]
    b = p.growth("Balyasny Asset Management", "2016-01", "2026-01")
    assert r(b["employees"], 1) == 7.2 and r(100 * (b["raum_per_employee"] - 1), 0) == 27
    assert [r(100 * x, 0) for x in b["advisory_share"]] == [64, 42]
    assert r(math.log(2) / 0.2) == 3.5 and r(100 * 360 * 5 / 7000, 0) == 26


def test_small_runs():
    """Fast property checks on small batches (CI): skill and a looser ladder lengthen tenure."""
    t_bad = tt.stop_times(0.0, p.VOL, p.TIGHT, 300, 5, np.random.default_rng(7))
    t_good = tt.stop_times(1.5, p.VOL, p.TIGHT, 300, 5, np.random.default_rng(8))
    t_loose = tt.stop_times(0.0, p.VOL, p.LOOSE, 300, 5, np.random.default_rng(7))
    assert np.isfinite(t_bad).mean() > np.isfinite(t_good).mean()
    assert np.isfinite(t_loose).mean() < np.isfinite(t_bad).mean()


@pytest.mark.reference
def test_table_printed():
    t = p.table()
    tight05, tight10 = t[("tight", 0.5)], t[("tight", 1.0)]
    assert (r(tight05["median"]), r(tight10["median"])) == (1.5, 3.6) and r(t[("tight", 0.0)]["median"]) == 0.9
    assert [r(100 * t[("tight", s)]["stopped"]) for s in p.SRS] == [99.6, 94.4, 74.8, 47.9]
    assert [r(100 * t[("tight", s)]["s1"]) for s in p.SRS] == [45.6, 60.2, 72.2, 81.8]
    assert [r(100 * t[("tight", s)]["s3"]) for s in p.SRS] == [15.9, 33.9, 53.5, 69.5]
    assert [r(100 * t[("tight", s)]["turnover"], 0) for s in p.SRS] == [63, 33, 16, 7]
    assert [r(100 * t[("loose", s)]["stopped"]) for s in (0.5, 1.0)] == [41.4, 15.3]
    assert [r(100 * t[("loose", s)]["s1"]) for s in (0.5, 1.0)] == [96.4, 98.7]
    assert [r(100 * t[("loose", s)]["s3"]) for s in (0.5, 1.0)] == [79.1, 92.8]
    assert [r(100 * t[("loose", s)]["turnover"], 0) for s in (0.5, 1.0)] == [6, 2]
    assert all(math.isinf(t[("loose", s)]["median"]) for s in (0.5, 1.0)) and math.isinf(t[("tight", 1.5)]["median"])


@pytest.mark.reference
def test_mixed_platform_and_checks():
    a, b = p.mixed(p.TIGHT), p.mixed(p.LOOSE)
    assert (r(100 * a["turnover"], 0), r(100 * b["turnover"], 0)) == (20, 5)
    assert (r(100 * a["first_year_stops"], 0), r(100 * b["first_year_stops"], 0)) == (35, 3)
    assert (r(100 * a["false_cut"], 0), r(100 * b["false_cut"], 0)) == (39, 14)
    base = tt.median_tenure(p.times(0.5, p.TIGHT))
    fine = tt.median_tenure(tt.stop_times(0.5, p.VOL, p.TIGHT, 4000, 10, np.random.default_rng(50), days=1008))
    assert abs(fine / base - 1) < 0.10 and r(fine) == 1.6
    nohalf = tt.median_tenure(tt.stop_times(0.5, p.VOL, tt.Ladder(1.0, 0.075), 4000, 10, np.random.default_rng(50)))
    assert r(nohalf) == 0.7
    v15 = tt.stop_times(1.0, 0.15, p.TIGHT, 4000, 10, np.random.default_rng(100))
    assert r(tt.median_tenure(v15)) == 0.9 and r(100 * np.isfinite(v15).mean()) == 98.6


def test_figure_gap_and_normal():
    rows = list(csv.DictReader(open(FIG)))
    first = next(x for x in rows if float(x["loose05"]) - float(x["tight05"]) > 0.40)
    assert first["years"] == "1.25" and (r(100 * float(first["loose05"])), r(100 * float(first["tight05"]))) == (94.5, 54.2)
    assert r(100 * 0.5 * (1 + math.erf(-1.5 / math.sqrt(2)))) == 6.7
