import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_fundterms as ft  # noqa: E402

T = ft.ff.FeeTerms(mgmt=0.0, perf=0.20)


def test_free_ride_and_series():
    rets = [-0.10, 0.10 / 0.9 + 0.0]   # down to 0.9, back to 1.0
    d = ft.pooled_vs_series(rets, [(0, 100.0), (1, 100.0)], T)
    assert d["pooled"][1] == 0.0                       # B bought at 0.9 and rode back to the mark for free
    assert math.isclose(d["series"][1], 0.2 * 100.0 * (1 / 0.9 - 1), rel_tol=1e-9)
    assert d["series"][0] == 0.0 and d["pooled"][0] == 0.0


def test_crystallisation_frequency():
    rets = [0.10, -0.10, 0.10, -0.10]
    monthly, yearly = ft.crystallised(rets, 0.2, 1), ft.crystallised(rets, 0.2, 4)
    assert monthly > yearly == 0.0


def test_redeem_policies():
    lad = [ft.Bucket(1, 0.3, 0.001), ft.Bucket(7, 0.2, 0.005), ft.Bucket(90, 0.5, 0.04)]
    a = ft.redeem(lad, 0.4, 7)
    assert math.isclose(a["cost"], 0.3 * 0.001 + 0.1 * 0.005)
    b = ft.redeem(lad, 0.4, 7, policy="pro_rata")
    assert b["cost"] > a["cost"]
    assert ft.ladder_share_within(a["ladder_after"], 7) < ft.ladder_share_within(b["ladder_after"], 7)
    g = ft.redeem(lad, 0.4, 7, gate=0.1)
    assert g["paid"] == 0.1 and math.isclose(g["deferred"], 0.3)
    s = ft.redeem(lad, 0.4, 7, swing=True)
    assert s["dilution_stayers"] == 0.0 and a["dilution_stayers"] > 0
    assert ft.max_redemption(lad, 7, 0.01) == 0.5
