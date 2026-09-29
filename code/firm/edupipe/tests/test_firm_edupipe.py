"""Acceptance tests for firm.edupipe."""
import pathlib
import sys
import zipfile

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_edupipe as fe  # noqa: E402


def test_read_ipeds(tmp_path):
    rows = ('﻿UNITID,CIPCODE,MAJORNUM,AWLEVEL,XCTOTALT,CTOTALT\n'
            '1,"27.0305",1,7,"R",10\n2,"27.0305",1,07,"R",5\n3,"27.0305",2,7,"R",99\n'
            '4,"27.0501",1,5,"R",7\n5,"11.0701",1,7,"R",3\n')
    p = tmp_path / "C2099_A.zip"
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("c2099_a.csv", rows.encode("utf-8"))
    got = fe.read_ipeds(p, ["27.0305", "27.0501"], ["5", "7"])
    assert got == {("27.0305", "7"): 15, ("27.0501", "5"): 7}


def test_placement_report():
    r = fe.PlacementReport("X", "2025", 100, 98, 98, 89, 145_000.0, "CSEA")
    assert r.placement_rate == 1.0 and r.reporting_rate == pytest.approx(89 / 98)
    lo, hi = r.median_quantile_bounds()
    assert lo == pytest.approx(40 / 89) and hi == pytest.approx(49 / 89)
    assert fe.PlacementReport("Y", "2025", None, 70, 67, None, 150_000.0, "").median_quantile_bounds() is None
