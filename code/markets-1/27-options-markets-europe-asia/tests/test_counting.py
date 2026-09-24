import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from counting import derive_2024, three_rankings


def test_derived_2024_total_matches_the_published_change():
    total_2024 = sum(derive_2024().values())
    assert total_2024 == pytest.approx(119.29 / (1 - 0.422), rel=0.005)


def test_the_largest_market_by_contracts_is_not_the_largest_by_premium():
    r = three_rankings()
    top = {k: max(v, key=v.get) for k, v in r.items()}
    assert top["contracts"].startswith("M1") and top["premium_usd"].startswith("M2")
    assert r["contracts"]["M1: weekly index options, small lots"] > 0.95
