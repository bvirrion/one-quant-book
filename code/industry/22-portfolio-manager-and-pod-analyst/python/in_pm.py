"""One Quant Book 17, chapter 22: the portfolio manager's deal and the pod analyst.

The deal: firm.roles.pm_deal on Book 16's firm.podshop pods, with ILLUSTRATIVE terms (no platform publishes its payout
rate or drawdown thresholds; one adviser's brochure describes the structure, ledger F1): capital, volatility, payout
rate, salary, cut and stop below. Utility: Book 17's firm.payoffer.certainty_equivalent. Pay evidence: the survey's
financial managers and financial and investment analysts in the securities industry (oews_roles.csv); the filings'
portfolio-manager family is too small to publish (lca_ranges.csv).
"""
import csv
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/roles"))
sys.path.insert(0, str(ROOT / "code/firm/payoffer"))
import firm_payoffer as po  # noqa: E402
import firm_roles as fr  # noqa: E402

DATA = ROOT / "data/industry"
YEARS, VOL, CAPITAL, RATE, SALARY = 3, 0.06, 500e6, 0.15, 0.5e6
CUT, STOP = 0.05, 0.075              # drawdowns from the tenure's peak, fractions of capital
ALTERNATIVE = 1.5e6                  # the salaried alternative, a year (illustrative)
RRA, WEALTH = 3.0, 5e6
SRS = tuple(x / 4 for x in range(0, 9))
N, SEED = 20_000, 22


def run(sr, n=N, seed=SEED, **kw):
    p = dict(years=YEARS, vol=VOL, capital=CAPITAL, rate=RATE, salary=SALARY, cut=CUT, stop=STOP)
    p.update(kw)
    return fr.pm_deal(sr, n=n, rng=np.random.default_rng(seed), **p)


def curve(n=N, **kw):
    out = []
    for sr in SRS:
        d = run(sr, n, **kw)
        out.append(dict(sr=sr, mean=float(d["pay"].mean()), p10=float(np.percentile(d["pay"], 10)),
                        p50=float(np.median(d["pay"])), p90=float(np.percentile(d["pay"], 90)),
                        stopped=float(d["stopped"].mean()),
                        ce=po.certainty_equivalent(d["pay"], RRA, WEALTH)))
    return out


def crossing(rows, key="mean", target=None):
    """Sharpe ratio at which the curve first reaches target (linear interpolation between grid points)."""
    target = YEARS * ALTERNATIVE if target is None else target
    for a, b in zip(rows, rows[1:], strict=False):
        if a[key] < target <= b[key]:
            w = (target - a[key]) / (b[key] - a[key])
            return a["sr"] + w * (b["sr"] - a["sr"]), a["stopped"] + w * (b["stopped"] - a["stopped"])
    return (rows[0]["sr"], rows[0]["stopped"]) if rows[0][key] >= target else (None, None)


def survey():
    with open(DATA / "oews_roles.csv") as f:
        return {(r["naics"], r["occ"]): r for r in csv.DictReader(f)
                if r["naics"] in ("523000", "525900") and r["occ"] in ("11-3031", "13-2051", "13-2099")}


def pm_filings():
    with open(DATA / "lca_ranges.csv") as f:
        return {(int(r["fy"]), r["kind"]): (int(r["n"]), int(r["employers"]), r["suppressed"] == "1")
                for r in csv.DictReader(f) if r["role"] == "portfolio manager" and r["level"] == "all"}


if __name__ == "__main__":
    rows = curve()
    for r in rows:
        print({k: round(v / 1e6, 2) if k in ("mean", "p10", "p50", "p90", "ce") else v for k, v in r.items()})
    print("cross mean", crossing(rows), "cross ce", crossing(rows, "ce"))
    print(pm_filings())
    for k, v in survey().items():
        print(k, v["occupation"], v["employment"], v["p10"], v["p50"], v["p90"])
