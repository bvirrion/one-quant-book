"""One Quant Book 17, chapter 30: choosing -- four offers, six attributes, uncertain weights.

Pay: chapter 13's three ILLUSTRATIVE offers (bank quant, market maker, platform analyst) and one more for a
technology firm's engineering job, valued with firm.payoffer over five years (10% leaving hazard, 5% discount rate).
Place: what tax and housing take from the average annual pay in each offer's city (firm.locations, chapter 27's
data). Hours: on-call nights a month (firm.workload; ILLUSTRATIVE rotas). Learning: the chooser's ILLUSTRATIVE
judgement on a 1-5 scale. Security: the share of five-year careers without an involuntary exit in the pay model (only
the platform's book can be closed). Weights: ILLUSTRATIVE swing points.
"""
import functools
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for sub in ("code/firm/careerdec", "code/firm/payoffer", "code/firm/locations", "code/firm/workload",
            "code/industry/13-how-pay-works/python", "code/industry/27-locations/python"):
    sys.path.insert(0, str(ROOT / sub))
import firm_careerdec as fd  # noqa: E402
import firm_locations as fl  # noqa: E402
import firm_payoffer as po  # noqa: E402
import firm_workload as fw  # noqa: E402
import in_locations as loc  # noqa: E402
import in_pay as pay  # noqa: E402

TECH = po.Package("technology engineer", 220_000.0, median=150_000.0, sigma=0.3, deferral=1.0, vest_years=4,
                  inst_vol=0.35)
OFFERS = ("bank quant", "market maker", "platform analyst", "technology engineer")
CITY = {"bank quant": "London", "market maker": "Chicago", "platform analyst": "New York",
        "technology engineer": "London"}
ONCALL = {"bank quant": 0.0, "market maker": fw.oncall_nights(365.25 / 12, 8), "platform analyst": 0.0,
          "technology engineer": fw.oncall_nights(365.25 / 12, 6)}
LEARNING = {"bank quant": 3.0, "market maker": 4.0, "platform analyst": 4.0, "technology engineer": 3.0}
ATTRS = ("expected pay", "pay risk", "tax and housing take", "on-call nights", "learning", "security")
HIGHER = (True, False, False, False, True, True)
SWING = (30.0, 15.0, 10.0, 15.0, 20.0, 10.0)
PAY_RISK = 1


@functools.cache
def sims():
    s = dict(pay.sims())
    s["technology engineer"] = po.simulate(TECH, pay.YEARS, pay.HAZARD, pay.RATE, pay.N,
                                           np.random.default_rng(pay.SEED + 40))
    s["bank quant"] = s.pop("bank")
    return s


def matrix():
    cities = loc.cities()
    rows = []
    for o in OFFERS:
        s = sims()[o]
        sm = po.summary(s)
        annual = sm["mean"] / pay.YEARS
        d = fl.disposable(loc.P, cities[CITY[o]], annual)
        cut = float(s["cut"].mean()) if "cut" in s else 0.0
        rows.append([sm["mean"], (sm["p90"] - sm["p10"]) / sm["mean"], 1.0 - d["disposable"] / annual, ONCALL[o],
                     LEARNING[o], 1.0 - cut])
    return np.array(rows)


def scaled():
    return fd.scale(matrix(), HIGHER)


def results(n=20_000, seed=30):
    s = scaled()
    w = fd.swing_weights(SWING)
    v = fd.value(s, w)
    ra = fd.rank_acceptability(s, n, np.random.default_rng(seed))
    return {"values": v, "best": int(np.argmax(v)), "dominated": fd.dominated(matrix(), HIGHER), "ra": ra,
            "flip": fd.flip_shift(s, w, PAY_RISK), "weights": w}


def ce3():
    return {o: po.certainty_equivalent(sims()[o]["pv"], 3.0, pay.WEALTH) for o in OFFERS}


if __name__ == "__main__":
    m = matrix()
    for o, row in zip(OFFERS, m, strict=True):
        print(o, [round(x, 3) for x in row])
    r = results()
    print({k: (np.round(v, 3) if isinstance(v, np.ndarray) else v) for k, v in r.items()})
    print({k: round(v) for k, v in ce3().items()})
