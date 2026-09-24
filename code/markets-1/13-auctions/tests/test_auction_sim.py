import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from auction_sim import EXAMPLE, curves, imbalance_impact, indicative_path, random_book


def test_curves_are_monotone():
    c = curves(EXAMPLE, 997, 1005)
    assert all(a[1] >= b[1] for a, b in zip(c, c[1:], strict=False))      # demand falls with price
    assert all(a[2] <= b[2] for a, b in zip(c, c[1:], strict=False))      # supply rises


def test_indicative_volume_only_grows():
    vols = [v for _, _, v, _ in indicative_path(random_book(600, 13), 1000)]
    assert vols[-1] >= vols[len(vols) // 2] >= vols[0]


def test_a_buy_imbalance_raises_the_price_and_more_so_when_larger():
    small, big = imbalance_impact(30, 0.10), imbalance_impact(30, 0.50)
    assert 0 <= small < big
