"""Chapter 13 of Book 2: the illustrative options behave as the text says."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/normalvol"))
from firm_normalvol import black
from swaption_demo import (
    ATM,
    EXPIRIES,
    black_equivalents,
    callable_swap,
    cap,
    load_negative_yields,
    no_black_below,
    smile,
)


def test_black_equivalent_falls_with_the_forward():
    rows = black_equivalents()
    vols = [b for _, b in rows]
    assert vols == sorted(vols, reverse=True) and rows[0][0] / 100 > no_black_below()


def test_collar_is_zero_cost_in_normal_but_not_in_black():
    c = cap()
    assert abs(c["collar"]) < 1e-6
    assert black(0.04, 0.045, 1, 0.25) > black(0.04, 0.035, 1, 0.25, payer=False)


def test_cube_and_smile_shapes():
    assert len(EXPIRIES) == len(ATM[10]) and all(ATM[2][i] >= ATM[30][i] for i in range(len(EXPIRIES)))
    assert smile(0) < smile(-2) and smile(0) < smile(2) and smile(-2) != smile(2)


def test_callable_signs():
    c = callable_swap()
    assert c["price"] > 0 and c["vega"] > 0 and c["delta"] < 0


def test_negative_yield_data():
    rows = load_negative_yields()
    de = [(d, x) for d, x, _ in rows if x < 0]
    assert len(de) == 38 and de[0][0] == "2016-06-01" and de[-1][0] == "2022-01-01"
