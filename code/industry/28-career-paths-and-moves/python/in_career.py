"""One Quant Book 17, chapter 28: career paths and moves -- the cost of a move and a career chain.

Every number here is ILLUSTRATIVE unless the ledger says otherwise: the package (base, award, deferral, vesting,
payment month), the notice, garden-leave and non-compete months, the buyout probability, the horizon, the career
chain's transition probabilities and pay by state, and the employer's garden-leave inputs. The laws that bound notice
and non-competes are in the chapter's dated boxes.
"""
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/careerpath"))
sys.path.insert(0, str(ROOT / "code/firm/gardenleave"))
sys.path.insert(0, str(ROOT / "code/firm/lineage"))
import firm_careerpath as fc  # noqa: E402
import firm_gardenleave as gl  # noqa: E402
import firm_lineage as fli  # noqa: E402

JOB = fc.Job(base=250_000.0, award=350_000.0, deferral=0.4, vest_years=3, pay_month=2)
MOVE = dict(notice_m=3, garden_m=3, noncompete_m=6, paid_noncompete=True, s=1.0)
HORIZON = 3
QS = (0.0, 0.25, 0.5, 0.75, 1.0)
MONTHS = tuple(range(1, 13))
CHAIN = fc.Chain(
    ("graduate", "researcher", "senior researcher", "portfolio manager", "left the industry"),
    ((0.60, 0.35, 0.00, 0.00, 0.05),
     (0.00, 0.65, 0.30, 0.00, 0.05),
     (0.00, 0.00, 0.80, 0.15, 0.05),
     (0.00, 0.00, 0.10, 0.85, 0.05),
     (0.00, 0.00, 0.00, 0.00, 1.00)),
    (250_000.0, 400_000.0, 700_000.0, 1_500_000.0, 200_000.0))
YEARS, N, SEED = 15, 20_000, 28
GARDEN = dict(P=5e6, L=0.2, lam=math.log(2) / 1.0, S=600_000.0)   # employer's view (Book 16, chapter 11)


def surface():
    return {(m, q): fc.breakeven_raise(JOB, m, HORIZON, q=q, **MOVE) for m in MONTHS for q in QS}


def by_month(q=0.5):
    return [fc.move_cost(JOB, m, q=q, **MOVE) for m in MONTHS]


def career():
    s = fc.simulate(CHAIN, "graduate", YEARS, N, np.random.default_rng(SEED))
    pay = fc.pay_paths(CHAIN, s)
    return {"mean": pay.mean(0), "p10": np.percentile(pay, 10, axis=0), "p50": np.median(pay, axis=0),
            "p90": np.percentile(pay, 90, axis=0),
            "cum_mean": pay.sum(1).mean(), "pm_by_10": float((s[:, 9] == 3).mean()),
            "left_by_10": float((s[:, 9] == 4).mean())}


def employer_view():
    return gl.best_length(GARDEN["P"], GARDEN["L"], GARDEN["lam"], GARDEN["S"])


def spinouts():
    return fc.spinouts(fli.Graph.load(ROOT / "data/industry/lineage.csv"))


if __name__ == "__main__":
    for m in (1, 2, 3, 6, 12):
        print(m, {q: round(100 * surface()[(m, q)], 1) for q in QS})
    for m, c in zip(MONTHS, by_month(), strict=True):
        print(m, {k: round(v) for k, v in c.items()})
    c = career()
    print([round(x) for x in c["mean"]], round(c["cum_mean"]), c["pm_by_10"], c["left_by_10"])
    print(employer_view(), len(spinouts()))
