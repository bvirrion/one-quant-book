import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import firm_privlink as p  # noqa: E402


def test_catalogue_and_alignment():
    P = p.load_paths()
    assert set(P) == {"peering_cpg", "peering", "endpoint_same", "endpoint_other", "internet"}
    assert all(x.source and x.as_of for x in P.values())
    assert not p.aligned("apne1-az4", ["apne1-az1", "apne1-az2"]) and p.aligned("apne1-az4", ["apne1-az4"])


def test_latency_order():
    P = p.load_paths()
    m = {k: p.rtt_percentiles(v, qs=(50,), n=20000)[50] for k, v in P.items()}
    assert m["peering_cpg"] < m["peering"] < m["endpoint_same"] < m["endpoint_other"] < m["internet"]
    assert m["endpoint_same"] - m["peering"] == pytest.approx(40, abs=3)


def test_costs_by_hand():
    P = p.load_paths()
    assert p.cost_per_million(P["endpoint_same"], 400) == pytest.approx(0.4 * 0.01)
    assert p.cost_per_million(P["endpoint_other"], 400) == pytest.approx(0.4 * 0.01 + 0.4 * 0.02)
    assert p.monthly_fixed(P["endpoint_same"], zones=2) == pytest.approx(0.014 * 2 * 730)
    assert p.cost_per_million(P["peering"]) == 0
