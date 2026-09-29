"""Numbers gate: every number printed in Book 14, chapter 8 (text and solutions)."""
import pathlib
import sys

import pytest
from scipy.optimize import brentq

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "python"))
import nw_servers as s  # noqa: E402

ss = s.ss


def test_reference_and_table():
    assert s.ref_ns() == 1528
    t = {r["name"]: r for r in s.table()}
    rows = {"AMD EPYC 9175F": (1491, 1659, 17, 272), "Intel Xeon Gold 6544Y": (1685, 1834, 19, 304),
            "AMD EPYC 9755": (1685, 2241, 8, 2048), "overclocked Xeon w7-2495X server": (1528, 1528, 5, 120)}
    for k, (hot, base, n, cores) in rows.items():
        r = t[k]
        assert (round(r["hot_ns"]), round(r["base_ns"]), r["servers"], r["cores"]) == (hot, base, n, cores)
    assert round(100 * (1 - 1491.328 / 1528), 1) == 2.4 and round(100 * (2241.0667 / 1528 - 1)) == 47
    assert t["AMD EPYC 9175F"]["server_w"] == 570 and t["AMD EPYC 9755"]["server_w"] == 1250
    t20 = {r["name"]: (r["servers"], r["cores"]) for r in s.table(cabinet_kw=20)}
    assert list(t20.values()) == [(35, 560), (38, 608), (16, 4096), (10, 240)]


def test_exercises():
    assert ss.path_ns(2000, 0.8, 5.0, 3.0) == pytest.approx(1360) and 0.2 * 2000 == 400
    assert int(15_000 // 570) == 26 and int(15_000 // 1250) == 12
    d = [ss.path_ns(1528, p, 4.0, 4.8) - ss.path_ns(1528, p, 5.0, 4.8) for p in (1.0, 0.6, 0.3)]
    assert [round(x) for x in d] == [367, 220, 110]
    assert brentq(lambda p: 1 - ss.path_ns(1, p, 5.0, 4.8) - 0.01, 0.01, 1) == pytest.approx(0.25)


def test_problem():
    assert round(2241.0667 / 1491.328, 2) == 1.50 and 1 / (1 - 0.6) == pytest.approx(2.5) and round(0.4 * 1528) == 611
    assert 3 * 570 + 4 * 1250 == 6710 and 3 * 16 >= 40 and 4 * 256 >= 1000
    p5 = brentq(lambda p: ss.path_ns(1, p, 2.7, 4.8) / ss.path_ns(1, p, 5.0, 4.8) - 1.05, 0.001, 1)
    assert round(100 * p5) == 6
    assert s.curve()[0][0] == 2.5
