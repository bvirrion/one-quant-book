"""Numbers gate: every numerical answer printed in Book 17, chapter 27 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import in_locations as a  # noqa: E402

fl = a.fl


def z(x):
    return round(float(x))


def test_table():
    t = a.table()
    want = {"London": (174_545, 35_324, 139_220), "New York": (183_982, 34_920, 149_062),
            "Chicago": (200_327, 21_372, 178_955), "Zurich": (207_691, 22_835, 184_855),
            "Hong Kong": (252_691, 37_753, 214_938)}
    assert {k: (z(v["net"]), z(v["rent"]), z(v["disposable"])) for k, v in t.items()} == want
    assert z(300_000 - t["London"]["net"]) == 125_455 and z(300_000 - t["Hong Kong"]["net"]) == 47_309
    assert z(t["Hong Kong"]["disposable"] - t["London"]["disposable"]) == 75_718
    assert z(t["Hong Kong"]["net"] - t["London"]["net"]) == 78_147
    assert z(t["Hong Kong"]["rent"] - t["London"]["rent"]) == 2_429
    assert z(t["London"]["rent"] - t["New York"]["rent"]) == 404


def test_london_new_york():
    x = a.london_new_york()
    assert round(x["crossing"], -2) == 851_900 and round(x["crossing_low"], -2) == 134_100
    assert (z(x["ny_for_london_300k"]), z(x["london_for_ny_300k"])) == (281_047, 318_569)
    m = a.table(1e6)
    assert (z(m["London"]["disposable"]), z(m["New York"]["disposable"])) == (510_220, 505_664)


def test_exercises():
    c = a.cities()
    assert z(fl.disposable(a.P, c["Chicago"], 280_000)["disposable"]) == 167_415
    hk = fl.City("HK", "hong_kong", a.HK_RENT_M2 * 110, "hkd", "x", "x", "x")
    d = fl.disposable(a.P, hk, 300_000)
    assert (z(d["rent"]), z(d["disposable"])) == (75_507, 177_185)
    assert 5942 * 12 == 71_304
    assert round(fl.at.local_per_usd(a.P, "london"), 3) == 0.758 and round(fl.at.local_per_usd(a.P, "hong_kong"), 2) == 7.80
    assert a.PLI_2024["Switzerland"] == 184.3


def test_curves():
    c = a.curves()
    d = [c["Hong Kong"][i] - c["London"][i] for i in range(len(a.GRID))]
    assert z(d[-1]) == 296_131 and d[a.GRID.index(300_000.0)] < 80_000 < d[a.GRID.index(350_000.0)]


def test_small_runs():
    assert set(a.cities()) == set(a.ORDER)
