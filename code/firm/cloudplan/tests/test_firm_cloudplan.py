import pathlib
import sys

import numpy as np
import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import firm_cloudplan as c  # noqa: E402


def test_zone_resolution():
    a = c.load_zones(c.DATA / "describe_az_account_a.json")
    b = c.load_zones(c.DATA / "describe_az_account_b.json")
    assert len(a) == len(b) == 6 and sorted(a.values()) == sorted(b.values())
    assert not c.same_physical(a, b, "us-east-1a") and c.same_physical(a, b, "us-east-1e")
    assert c.locate(b, a["us-east-1a"]) == "us-east-1b"


def test_probability_by_simulation():
    rng = np.random.default_rng(0)
    n, trials = 6, 20000
    same = sum(rng.permutation(n)[0] == rng.permutation(n)[0] for _ in range(trials))
    assert same / trials == pytest.approx(c.p_same_name_same_zone(n), abs=0.01)
    assert c.expected_penalty_us(3, 270, 555) == pytest.approx(190)


def test_rtt_fit_and_costs():
    x = c.sample_rtt(c.Rtt(270, 395), 200000, seed=2)
    assert np.percentile(x, 50) == pytest.approx(270, rel=0.01) and np.percentile(x, 99) == pytest.approx(395, rel=0.02)
    cat = c.load_catalogue()
    assert cat["c7i.metal-24xl"].bare_metal and not cat["c7i.4xlarge"].bare_metal
    m = c.monthly_cost([("c7i.4xlarge", 2)], cat, cross_zone_gb=1000)
    assert m["compute"] == pytest.approx(2 * 0.714 * 730) and m["transfer"] == pytest.approx(20.0)
