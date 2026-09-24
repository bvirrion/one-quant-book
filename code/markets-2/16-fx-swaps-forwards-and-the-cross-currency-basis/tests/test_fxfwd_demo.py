"""Chapter 16 of Book 2: data and demo behave as the text says."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from fxfwd_demo import load_hedged, load_swaplines, points_curve


def test_points_grow_with_tenor_and_basis_adds():
    rows = points_curve()
    assert all(a > b for (_, _, a, _), (_, _, b, _) in zip(rows, rows[1:], strict=False))
    assert all(wb < nb for _, _, nb, wb in rows)


def test_data_files():
    h = load_hedged()
    assert len(h) == 101 and h[0][0] == "2018-04-30" and h[-1][0] == "2026-08-31"
    s = dict(load_swaplines())
    assert max(v for d, v in s.items() if d < "2012") > 550 and max(v for d, v in s.items() if "2019" < d < "2022") > 440
