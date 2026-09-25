import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_flowmm import FlowConfig, client_hits, client_markouts, price_clients, run_desk, simulate_flow  # noqa: E402

CFG = FlowConfig(requests=20_000)


def test_mid_path_does_not_depend_on_the_desk():
    f = simulate_flow(CFG)
    a, b = run_desk(f, CFG, 0.5), run_desk(f, CFG, 3.0)
    assert a["volume"] > b["volume"] and np.isclose(a["net"], a["capture"] + a["marks"] - a["hedge_cost"])


def test_markouts_separate_the_types():
    f = simulate_flow(CFG)
    m = client_markouts(run_desk(f, CFG, 1.0), f, CFG)
    assert np.nanmean(m[f["types"] == 2]) > np.nanmean(m[f["types"] == 1]) > np.nanmean(m[f["types"] == 0])


def test_pricing_by_hand_and_hit_ratios():
    cfg = FlowConfig()
    h = price_clients(np.array([0.0, 5.0]), np.array([0.5, 0.5]), 1.0, cfg)
    assert h[1] > 4.99 and 0.5 < h[0] < 1.5                          # a toxic client is priced out, a neutral one kept
    f = simulate_flow(CFG)
    r = run_desk(f, CFG, 1.0)
    hits = client_hits(r, f)
    assert ((hits >= 0) & (hits <= 1)).all() and np.isclose(hits @ np.bincount(f["client"], minlength=90), r["volume"])


def test_hedging_keeps_inventory_within_the_limit():
    f = simulate_flow(CFG)
    r = run_desk(f, CFG, 0.5)
    assert r["abs_inventory"] <= CFG.limit and 0 < r["internalised"] <= 1
