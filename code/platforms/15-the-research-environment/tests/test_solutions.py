"""Numbers gate: every numerical answer printed in One Quant Book 15, chapter 15 (text and solutions)."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import pl_envaudit as P
import research_lib as L


def test_small_runs(tmp_path):
    r = P.study(tmp_path)
    assert (r["saved"], r["rerun_ok"], r["corrected"]) == ("1.96", False, "2.44")
    assert r["rerun_error"] == "NameError: name 'exclude' is not defined"
    assert [(f.kind, f.cell) for f in r["findings"]] == [("out-of-order", 3), ("skipped-counter", -1),
                                                          ("never-defined", 4)]
    assert (r["library"], r["library_excluding"], r["pooled"], r["country_years"]) == ("2.44", "1.96", "2.90", 455)
    c = P.reproduce(tmp_path / "clean", tmp_path)
    assert c["result"] == "2.44" and c["data_diffs"] == []


def test_library_function():
    df = P.panel()
    assert L.average_growth(df, 90, since=1950) == pytest.approx(2.44, abs=0.005)
    with pytest.raises(ValueError):
        L.average_growth(df, weight="median")
    tiny = P.pd.DataFrame({"country": ["A", "A", "B"], "year": [1, 2, 1], "debt": [95, 95, 95], "growth": [0.0, 2.0, 4.0]})
    assert L.average_growth(tiny) == 2.5 and L.average_growth(tiny, weight="country-year") == 2.0
    assert L.average_growth(tiny, exclude=["B"]) == 1.0


@pytest.mark.reference
def test_environment_matches_the_lock(tmp_path):
    P.study(tmp_path)
    assert P.reproduce(tmp_path / "clean", tmp_path)["env_diffs"] == []


def test_panel_facts():
    df = P.panel()
    assert len(df) == 20 * 64 and df["country"].nunique() == 20
    hi = df[(df.debt > 90) & (df.year >= 1950)]
    assert hi[hi.country.isin(P.EXCLUDED)].shape[0] == 204 and hi.country.nunique() == 16


def test_choices_chart():
    import csv
    rows = list(csv.DictReader(open(pathlib.Path(__file__).resolve().parents[4]
                                    / "figdata/platforms/15-the-research-environment/choices.csv")))
    got = {r["case"]: (r["by_country"], r["by_country_year"]) for r in rows}
    assert got["five excluded; all years"] == ("1.96", "2.20") and got["all countries; from 1950"] == ("2.44", "2.90")
