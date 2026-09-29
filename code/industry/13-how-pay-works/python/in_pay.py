"""One Quant Book 17, chapter 13: how pay works -- three stylised offers valued with firm.payoffer.

Every parameter below is ILLUSTRATIVE: chosen to show the mechanics, not taken from any firm. Where a public rule
bounds a parameter, the chapter cites it (a 40% minimum deferral over four years for UK material risk takers; one
bank's three-year delivery of restricted stock units). Amounts in US dollars; five years of employment, a voluntary
leaving hazard of 10% a year, a 5% discount rate, and 500,000 of other wealth for the certainty equivalents.
"""
import functools
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/payoffer"))
import firm_payoffer as po  # noqa: E402

YEARS, HAZARD, RATE, WEALTH, N, SEED = 5, 0.10, 0.05, 500_000.0, 20_000, 13
BANK = po.Package("bank", 250_000.0, median=200_000.0, sigma=0.5, deferral=0.40, vest_years=4, inst_vol=0.30)
MAKER = po.Package("market maker", 200_000.0, median=250_000.0, sigma=0.8)
PLATFORM = po.Package("platform analyst", 175_000.0, share=0.02, pnl_mean=15e6, pnl_sd=20e6, cut=-10e6,
                      sign_on=100_000.0, sign_on_years=1, guarantee=150_000.0)
OFFERS = (BANK, MAKER, PLATFORM)
RRAS = (0.5, 1.0, 2.0, 3.0, 4.0, 5.0)


@functools.cache
def sims():
    return {p.name: po.simulate(p, YEARS, HAZARD, RATE, N, np.random.default_rng(SEED + i))
            for i, p in enumerate(OFFERS)}


def table():
    out = {}
    for p in OFFERS:
        s = sims()[p.name]
        sm = po.summary(s)
        sm["ce1"] = po.certainty_equivalent(s["pv"], 1.0, WEALTH)
        sm["ce3"] = po.certainty_equivalent(s["pv"], 3.0, WEALTH)
        sm["p25"], sm["p75"] = (float(np.percentile(s["pv"], q)) for q in (25, 75))
        out[p.name] = sm
    return out


def ce_curve():
    return {p.name: [po.certainty_equivalent(sims()[p.name]["pv"], r, WEALTH) for r in RRAS] for p in OFFERS}


def bank_unvested():
    """The bank offer for a stayer: expected unvested balance at the end of each year, at grant value."""
    s = po.simulate(BANK, YEARS, 0.0, RATE, N, np.random.default_rng(SEED + 10), leave_year=YEARS + 1)
    return [float(s["unvested"][:, t].mean()) for t in range(YEARS)]


def forfeit_by_year():
    """Expected present value forfeited by leaving the bank at the end of year k (k = 1..5)."""
    return [float(po.simulate(BANK, YEARS, 0.0, RATE, N, np.random.default_rng(SEED + 20 + k),
                              leave_year=k)["forfeited"].mean()) for k in range(1, YEARS + 1)]


def buyout_year2():
    return po.buyout(BANK, 2, N, np.random.default_rng(SEED + 30))


def platform_cut_share():
    return float(sims()["platform analyst"]["cut"].mean())


if __name__ == "__main__":
    for k, v in table().items():
        print(k, {a: round(b) if abs(b) > 10 else round(b, 3) for a, b in v.items()})
    print({k: [round(x) for x in v] for k, v in ce_curve().items()})
    print([round(x) for x in bank_unvested()], [round(x) for x in forfeit_by_year()], round(buyout_year2()))
    print(platform_cut_share())
