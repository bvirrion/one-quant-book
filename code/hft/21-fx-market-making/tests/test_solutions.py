"""Numbers gate: every numerical answer printed in Book 11, chapter 21 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import hf_fx as h  # noqa: E402


def r(x, d=3):
    return round(float(x), d)


def test_venues_and_cross():
    v = h.venues()
    assert (r(v["consolidated"], 2), r(v["primary"], 2)) == (0.26, 0.30)
    b, a = h.cross()
    assert (r(b), r(a), round((a - b) * 100, 1)) == (162.967, 162.993, 2.6)
    assert r(h.fx.fair_price([1.08500, 1.08503], [0.3, 0.6], [0, 0], 0.05)[0], 6) == 1.085006


def test_last_look():
    ll = h.last_look()
    got = {p: [(r(ll[p][t]["capture"]), r(100 * ll[p][t]["reject"], 1)) for t in ("tier 1", "tier 2", "tier 3", "all")]
           for p in ll}
    assert got["none"] == [(0.125, 0.0), (0.453, 0.0), (1.008, 0.0), (0.4, 0.0)]
    assert got["asymmetric"] == [(0.2, 43.5), (0.395, 26.5), (0.851, 18.3), (0.389, 33.4)]
    assert got["symmetric"] == [(0.14, 56.8), (0.28, 43.1), (0.637, 37.0), (0.282, 48.8)]
    assert r(ll["asymmetric"]["tier 1"]["reject_uninformed"] * 100, 0) == 19
    long_hold = h.fx.stream(dict(h.TIERS), hold=20.0, policy="asymmetric")
    assert r(100 * long_hold["tier 3"]["reject_uninformed"], 1) == 32.6


def test_hedging():
    g = h.hedging()
    assert round(g[0.0]["best"], 2) == 0.95
    assert [(round(g[s]["half_life"]), round(100 * g[s]["best"])) for s in (0.0003, 0.0004, 0.00045, 0.0005)] == [
        (1155, 95), (866, 80), (770, 50), (693, 5)]
    assert round(g[0.001]["half_life"]) == 347 and round(g[0.001]["internalise_all"] / 10) == 588 and g[0.001]["hedge_all"] == 3000
    b, res = h.fx.best_hedge_share(skew=0.0)
    assert round(100 * (1 - 5000 / (2 * 0.002 * res[0.0]["risk_sd"] ** 2))) == 97
