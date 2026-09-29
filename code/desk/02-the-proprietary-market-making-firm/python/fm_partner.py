"""One Quant Book 16, chapter 2: the proprietary market-making firm as a partnership.

The chapter's firm (illustrative parameters, $ millions): trading capital of 200 supports daily volume of
capital / 0.02 (a prime broker's requirement of 2 per cent of daily volume) up to the 20,000 a day its markets
can give it; it captures 1 basis point at technology parity; its competitors' technology grows 15 per cent a
year and its own depreciates 20 per cent a year; fixed costs 60 a year; variable pay 25 per cent of the result.
"""
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/partnership"))
import firm_partnership as fp  # noqa: E402

BASE = fp.Params(margin=0.02, market=20_000.0)
RATE = 0.10                       # partners' discount rate
GRID = np.round(np.arange(0.0, 1.0001, 0.05), 2)


def params(**kw):
    d = dict(BASE.__dict__)
    d.update(kw)
    return fp.Params(**d)


def retention_curve(p=BASE, grid=GRID, terminal=0.0):
    return np.array([fp.discounted_payout(fp.simulate(p, r), RATE, terminal) for r in grid])


def best_retention(p=BASE, terminal=0.0):
    v = retention_curve(p, terminal=terminal)
    i = int(np.argmax(v))
    return float(GRID[i]), float(v[i])


def years_to_fill(p=BASE, retention=0.5):
    """First year (1-based) in which trading capital reaches what the market can use."""
    s = fp.simulate(p, retention)
    full = p.market * p.margin
    idx = np.nonzero(s["capital"] >= full)[0]
    return int(idx[0]) + 1 if len(idx) else None


def treadmill(years=25):
    """Steady spending (holds parity) against 25 per cent of the stock, over a long horizon, retention 0.2."""
    out = {}
    for name, share in (("steady", fp.steady_spend_share(BASE.g, BASE.d)), ("lean", 0.25)):
        out[name] = fp.simulate(params(spend_share=share, years=years), 0.2)
    return out


def profit_gone_year(sim):
    idx = np.nonzero(sim["profit"] <= 0)[0]
    return int(idx[0]) + 1 if len(idx) else None


def regulatory(p=BASE, deriv_share=0.0):
    """Own funds requirement for year 1: fixed overheads = fixed costs + technology spending; daily trading flow
    = the year's volume (cash trades unless deriv_share > 0); no net-position charge (the book is flat daily)."""
    s = fp.simulate(p, 0.2)
    vol = s["volume"][0]
    fo = p.people + s["spend"][0]
    return fp.own_funds_requirement(fo, vol * (1 - deriv_share), vol * deriv_share, 0.0), fo, vol


def accounts(retention=0.2, depart_year=5, depart_points="b", repay_years=3):
    """Four members with points 40/30/20/10, each starting with a quarter of the capital. Member b leaves at the
    end of depart_year and is repaid over repay_years; the firm's capital is what the members leave in."""
    ps = fp.Partnership([fp.Member(n, pts, BASE.capital0 / 4) for n, pts in (("a", 40), ("b", 30), ("c", 20),
                                                                                  ("d", 10))])
    cap, tech, front = BASE.capital0, BASE.tech0, BASE.tech0
    rows = []
    for t in range(BASE.years):
        spend = BASE.spend_share * tech
        vol = min(cap / BASE.margin, BASE.market)
        rev = float(fp.capture(tech / front, BASE.c0, BASE.eta)) * vol * BASE.days
        pre = rev - BASE.people - spend
        prof = pre - BASE.var_pay * max(pre, 0.0)
        draws = ps.allocate(prof, 1 - retention)
        repaid = ps.pay_departures()
        if t + 1 == depart_year:
            ps.depart(depart_points, repay_years)
        cap = sum(m.capital for m in ps.members) + sum(a * n for a, n in ps.leaving.values())
        rows.append({"year": t + 1, "profit": prof, "draws": sum(draws.values()), "repaid": repaid, "capital": cap,
                     "volume": vol})
        tech = (1 - BASE.d) * tech + spend
        front = (1 + BASE.g) * front
    return rows


def target_value(target=None):
    """Discounted payout of the target-capital policy (default target: the capital the market can use)."""
    target = BASE.market * BASE.margin if target is None else target
    return fp.discounted_payout(fp.simulate(BASE, fp.target_capital(target)), RATE)


def year1():
    s = fp.simulate(BASE, 0.2)
    return {"volume": s["volume"][0], "revenue": s["revenue"][0], "spend": s["spend"][0], "profit": s["profit"][0]}


def growing_market(growth=0.10, years=25):
    return fp.simulate(params(spend_share=fp.steady_spend_share(BASE.g, BASE.d), years=years, market_growth=growth),
                       0.2)
