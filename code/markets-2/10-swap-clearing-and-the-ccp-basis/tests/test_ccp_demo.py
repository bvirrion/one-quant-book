"""Chapter 10 of Book 2: the illustrative clearing-house margin model behaves as the text says."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from ccp_demo import MODEL, basis_table, im_profiles, one_way_book


def test_margin_declines_to_zero():
    rows = im_profiles()
    yearly = [r[2] for r in rows if r[0] == int(r[0])]         # between payments it drifts up
    assert all(a > b for a, b in zip(yearly, yearly[1:], strict=False))
    assert rows[0][2] > rows[0][1] > 0


def test_basis_grows_with_maturity_and_funding():
    table = basis_table()
    for col in (1, 2, 3):
        vals = [r[col] for r in table]
        assert vals == sorted(vals)
    for _, a, b, c in table:
        assert math.isclose(b, 2 * a) and math.isclose(c, 3 * a)


def test_mpor_scaling_and_linearity():
    b = one_way_book()
    assert math.isclose(b["im_10day"] / b["im"], math.sqrt(2))
    small = one_way_book(notional=1e8)
    assert math.isclose(b["mva"] / small["mva"], 20)
    assert math.isclose(b["basis_one"], small["basis_one"])
    assert MODEL.mpor_days == 5.0
