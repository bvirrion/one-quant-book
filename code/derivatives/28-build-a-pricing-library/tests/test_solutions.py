"""Numbers gate: every numerical answer printed in Book 5, Chapter 28 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from dv_library import (
    ONE_YEAR,
    book_prices,
    bucket_profile,
    crn_noise,
    crn_noise_big,
    engine_table,
    node_vega,
    scenario_grid,
)


def test_book_and_engines():
    p = book_prices()
    assert round(p["total"]) == -928_523
    assert {k: v["engine"] for k, v in p.items() if k != "total"} == {
        "CALL-1Y-100": "Analytic", "AMPUT-1Y-95": "Tree", "DOC-1Y-100-80": "ClosedForm", "VARSWAP-1Y": "ClosedForm",
        "AUTOCALL-3Y": "MonteCarlo"}
    e = engine_table()
    c, a = e["CALL-1Y-100"], e["AMPUT-1Y-95"]
    assert [round(c[k], 4) for k in ("Analytic", "Tree", "PDE", "MonteCarlo")] == [8.5437, 8.5437, 8.5413, 8.5415]
    assert [round(a[k], 4) for k in ("Tree", "PDE")] == [5.0731, 5.0702]
    assert abs(c["Analytic"] - c["Tree"]) < 2e-6 and round(c["Analytic"] - c["PDE"], 4) == 0.0024


def test_node_vega_and_noise():
    n = node_vega()
    assert (round(n["AMPUT-1Y-95"]), round(n["VARSWAP-1Y"]), round(n["AUTOCALL-3Y"]), round(n["total"])) == (-88, -90, 2_249, 2_072)
    assert n["CALL-1Y-100"] == 0.0 and n["DOC-1Y-100-80"] == 0.0
    c = crn_noise()
    assert (round(c["sd_with"]), round(c["sd_without"]), round(c["ratio"], 1)) == (51, 217, 4.3)
    big = crn_noise_big()
    assert (round(big["sd"], 1), round(big["mean"])) == (25.1, 2_231)
    assert round(c["sd_with"], 1) == 50.8


def test_profile_and_scenarios():
    b = bucket_profile()
    by = {e.year: v for e, v in b["by_expiry"].items() if v != 0.0}
    assert (round(by[2027]), round(by[2028]), round(by[2029])) == (2_275, 1_464, 3_008)
    assert all(v == 0.0 for e, v in b["by_expiry"].items() if e < ONE_YEAR)
    assert (round(sum(b["by_expiry"].values())), round(b["parallel"])) == (6_747, 6_706)
    g = scenario_grid()
    assert (round(g["crash: -20%, +10 vol"] / 1000, 1), round(g["spot +10%"] / 1000, 1), round(g["vol -5"] / 1000, 1)) == (161.8, -24.0, -34.9)
