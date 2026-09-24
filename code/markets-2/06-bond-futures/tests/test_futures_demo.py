"""Tutorial of Book 2, Chapter 6: the printed end state is reproduced."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from futures_demo import ctd_at, fair_futures, switch_shift, table


def test_table_as_printed():
    assert fair_futures() == 111.765625
    rows = {r["name"]: r for r in table()}
    expect = {"3 7/8 Aug-33": (99.132, 0.8870, -0.004, 0.020, 3.82), "4 1/8 Nov-33": (100.549, 0.8971, 0.284, 0.261, 2.95),
              "4 1/4 Feb-34": (101.262, 0.9012, 0.539, 0.488, 2.12), "4 5/8 May-34": (103.641, 0.9200, 0.817, 0.695, 1.45),
              "4 Aug-34": (99.462, 0.8806, 1.041, 1.036, 0.05)}
    for name, (clean, cf, gross, net, irr) in expect.items():
        r = rows[name]
        assert (round(r["clean"], 3), r["cf"], round(r["gross"], 3), round(r["net"], 3), round(r["irr"] * 100, 2)) == (
            clean, cf, gross, net, irr)
    assert max(rows.values(), key=lambda r: r["irr"])["name"] == "3 7/8 Aug-33"


def test_switch():
    assert ctd_at(0.0) == "3 7/8 Aug-33"
    (s, old, new), = switch_shift()
    assert round(s * 1e4) == 147 and (old, new) == ("3 7/8 Aug-33", "4 Aug-34")
