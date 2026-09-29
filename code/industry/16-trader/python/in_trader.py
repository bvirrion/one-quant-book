"""One Quant Book 17, chapter 16: the trader: pay evidence and the load of one person supervising many algorithms.

Pay: data/industry/lca_ranges.csv and oews_finance.csv (chapter 14). Supervision: firm.roles with ILLUSTRATIVE rates
(each strategy raises alerts at `a` per hour; handling takes 30 seconds on average; the standard is that at most 1% of
alerts wait more than one minute).
"""
import csv
import functools
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/roles"))
import firm_roles as fr  # noqa: E402

DATA = ROOT / "data/industry"
H, T, P = 30.0, 60.0, 0.01
RATES = (0.5, 1.0, 2.0, 4.0)
SIGMA = math.sqrt(math.log(1 + 1.5 ** 2))  # lognormal handling with mean 30 s and standard deviation 45 s
MU = math.log(H) - SIGMA ** 2 / 2


def pay():
    with open(DATA / "lca_ranges.csv") as f:
        rows = list(csv.DictReader(f))
    cells = {lvl: fr.lca_cells(rows, "trader", 2025, lvl) for lvl in ("all", "I", "II", "III", "IV")}
    with open(DATA / "oews_finance.csv") as f:
        oews = {(r["naics"], r["occ"]): r for r in csv.DictReader(f)}
    return cells, oews[("523000", "41-3031")]


def capacity():
    return {a: fr.max_strategies(a, H, T, P) for a in RATES}, {a: fr.max_strategies(a, H, 300.0, P) for a in RATES}


def lognormal(n, rng):
    return rng.lognormal(MU, SIGMA, n)


@functools.cache
def tails(max_n=20, a=1.0, n_sim=400_000, seed=7):
    """P(wait > 60 s) against the number of strategies: M/M/1 closed form and lognormal handling by simulation."""
    out = []
    for n in range(1, max_n + 1):
        lam = n * a / 3600.0
        out.append((n, fr.mm1_wait_tail(lam, 1.0 / H, T),
                    fr.lindley_tail(lam, lognormal, T, n_sim, np.random.default_rng(seed + n))))
    return out


if __name__ == "__main__":
    c, o = pay()
    print(c["all"], o["p50"])
    print(capacity())
    for row in tails()[:12]:
        print(row)
