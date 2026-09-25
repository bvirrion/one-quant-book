"""Acceptance tests of firm.synthmkt: determinism, bookkeeping, point-in-time fundamentals, the stylised facts and the
planted predictors (statistical properties over several seeds, never on one path)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_synthmkt import MarketConfig, simulate

SMALL = MarketConfig(n=300, days=1260, seed=2)
P = simulate(SMALL)


def test_deterministic_and_counts():
    q = simulate(SMALL)
    assert np.array_equal(np.nan_to_num(P.ret), np.nan_to_num(q.ret)) and P.delist == q.delist
    assert (P.listed.sum(axis=1) == 300).all()
    assert all(P.ret[d, p] == r for p, (d, _, r) in P.delist.items())
    assert all(not P.listed[d + 1:, p].any() for p, (d, _, _) in P.delist.items() if d + 1 < P.ret.shape[0])


def test_secmaster_agrees_with_the_panel():
    sm = P.secmaster
    for p in range(0, P.ret.shape[1], 37):
        assert sm.ticker(p, int(P.start[p])) is not None
        if p in P.delist:
            assert sm.delisting(p)[0] == P.delist[p][0]


def test_fundamentals_are_point_in_time():
    f = P.fundamentals
    assert all(x["filed"] > x["fiscal_end"] for x in f)
    restated = [x for x in f if x["restated"] >= 0]
    assert restated and all(x["restated"] > x["filed"] and x["field"] == "eps" for x in restated)
    s = P.fundamentals_store()
    x = restated[0]
    assert s.asof(x["pid"], "eps", x["fiscal_end"], x["filed"] - 1) is None
    assert s.asof(x["pid"], "eps", x["fiscal_end"], x["filed"]) == x["value"]
    assert s.asof(x["pid"], "eps", x["fiscal_end"], x["restated"]) == x["restated_value"]


def _ic(sig, ret, listed, h=1, step=5, burn=260):
    out = []
    T = ret.shape[0]
    for t in range(burn, T - h, step):
        fwd = np.nansum(ret[t + 1:t + 1 + h], axis=0) if h > 1 else ret[t + 1]
        ok = ~np.isnan(sig[t]) & ~np.isnan(fwd) & listed[t]
        if ok.sum() > 50:
            a = np.argsort(np.argsort(sig[t][ok]))
            b = np.argsort(np.argsort(fwd[ok]))
            out.append(np.corrcoef(a, b)[0, 1])
    return float(np.mean(out))


def test_stylised_facts_and_planted_predictors_over_seeds():
    kurt, acf20, lev, rev, mom = [], [], [], [], []
    for seed in (1, 3, 5):
        p = simulate(MarketConfig(n=400, days=1512, seed=seed))
        m = p.mkt - p.mkt.mean()
        kurt.append((m**4).mean() / (m**2).mean() ** 2)
        a = np.abs(m)
        acf20.append(np.corrcoef(a[:-20], a[20:])[0, 1])
        lev.append(np.corrcoef(m[:-1], m[1:] ** 2)[0, 1])
        rev.append(_ic(-p.ret, p.ret, p.listed))
        cs = np.cumsum(np.log1p(np.nan_to_num(p.ret)), axis=0)
        mo = np.full_like(p.ret, np.nan)
        mo[252:] = cs[231:-21] - cs[:-252]
        mom.append(_ic(mo, p.ret, p.listed, h=21, step=21))
    assert min(kurt) > 5 and min(acf20) > 0.05 and max(lev) < 0
    assert min(rev) > 0.01 and np.mean(mom) > 0.0


def test_cross_section_has_a_dominant_factor():
    x = P.ret[-252:]
    x = x[:, ~np.isnan(x).any(axis=0)]
    ev = np.linalg.eigvalsh(np.corrcoef(x.T))[::-1]
    assert 0.1 < ev[0] / ev.sum() < 0.5 and ev[0] > 3 * ev[1]


def test_point_in_time_styles_match_the_simulation():
    from firm_synthmkt import point_in_time_styles
    P = simulate(MarketConfig(n=200, days=600, seed=3))
    st = point_in_time_styles(P)
    last = P.ret.shape[0] - 1
    alive = P.listed[last]
    assert np.allclose(st["momentum"][last, alive], P.style_x[alive, 2], atol=1e-6)   # set on day 588, kept since
    lb = st["log_bp"][last - 1, alive]
    ok = np.isfinite(lb)
    z = (lb[ok] - lb[ok].mean()) / lb[ok].std()
    assert ok.mean() > 0.9 and np.corrcoef(z, P.style_x[alive, 1][ok])[0, 1] > 0.99
    assert np.all(np.isnan(st["log_bp"][:21][P.listed[:21]]))                        # nothing filed yet


def test_ou_level_is_optional_and_mean_reverting():
    base = simulate(MarketConfig(n=200, days=600, seed=3))
    ou = simulate(MarketConfig(n=200, days=600, seed=3, ou_share=0.3))
    assert "ou" not in base.alpha and "ou" in ou.alpha
    assert np.array_equal(base.mkt, ou.mkt) and np.array_equal(base.industry[:200], ou.industry[:200])
    a, r = ou.alpha["ou"][:-1], ou.ret[1:]
    ok = np.isfinite(a) & np.isfinite(r)
    assert np.corrcoef(a[ok], r[ok])[0, 1] > 0.05


def test_twins_are_optional_and_cointegrated():
    base = simulate(MarketConfig(n=200, days=600, seed=3))
    tw = simulate(MarketConfig(n=200, days=600, seed=3, twin_share=0.2))
    assert base.twin is None and np.array_equal(base.mkt, tw.mkt)
    p = np.flatnonzero(tw.twin[:200] >= 0)
    assert len(p) == 40
    q = tw.twin[p]
    ok = tw.listed[:, p].all(axis=0) & tw.listed[:, q].all(axis=0)
    a, b = p[ok][0], q[ok][0]
    spread = np.log(np.cumprod(1 + tw.ret[:, a])) - np.log(np.cumprod(1 + tw.ret[:, b]))
    assert spread.std() < 0.04 and abs(np.corrcoef(spread[1:], spread[:-1])[0, 1] - np.exp(-1 / 10)) < 0.1
