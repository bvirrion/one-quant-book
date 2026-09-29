"""One Quant Book 17, chapter 18: bank quants -- pay evidence, reporting lines and the validation workload.

Pay: chapter 14's LCA tables (bank employers) and the BLS occupational survey (oews_roles.csv). Reporting lines:
firm.roles.independence on an ILLUSTRATIVE bank organisation. Workload: an ILLUSTRATIVE inventory tiered by Book 6's
firm.modelval rule (materiality, complexity and uncertainty scores; tier -> revalidation interval), with ILLUSTRATIVE
hours per validation and review; no bank publishes these figures.
"""
import csv
import itertools
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/roles"))
sys.path.insert(0, str(ROOT / "code/firm/modelval"))
import firm_modelval as mv  # noqa: E402
import firm_roles as fr  # noqa: E402

DATA = ROOT / "data/industry"
LEVELS = ("I", "II", "III", "IV")
SCORE_P = (0.5, 0.3, 0.2)            # P(score 1, 2, 3) for materiality, complexity and uncertainty (illustrative)
MODELS = 1000
FULL = {1: 400.0, 2: 160.0, 3: 60.0}   # hours of a full independent validation, by tier (illustrative)
REVIEW = {1: 40.0, 2: 16.0, 3: 8.0}    # hours of a periodic review in a year without full validation (illustrative)
CHANGE = 0.10                          # share of models with a material change a year, fully revalidated
PRODUCTIVE = 1600.0                    # hours of validation work a validator delivers a year (illustrative)


def lca():
    with open(DATA / "lca_ranges.csv") as f:
        rows = list(csv.DictReader(f))
    out = {}
    for fy in (2021, 2025):
        for role in ("quant researcher", "risk"):
            for lvl in ("all",) + LEVELS:
                c = fr.lca_cells(rows, role, fy, lvl).get("bank")
                if c is not None:
                    out[(fy, role, lvl)] = c
    return out


def oews(occs=("13-2054", "13-2099", "15-2031", "13-2051"), naics=("5220A1", "523000")):
    with open(DATA / "oews_roles.csv") as f:
        return {(r["naics"], r["occ"]): r for r in csv.DictReader(f) if r["naics"] in naics and r["occ"] in occs}


def growth(fy0=2021, fy1=2025):
    with open(DATA / "cpi_usa.csv") as f:
        cpi = {int(r["year"]): float(r["cpi"]) for r in csv.DictReader(f)}
    c = lca()
    nominal = c[(fy1, "quant researcher", "all")]["p50"] / c[(fy0, "quant researcher", "all")]["p50"]
    return nominal, nominal * cpi[fy0] / cpi[fy1]


def tier_shares(p=SCORE_P):
    share = {1: 0.0, 2: 0.0, 3: 0.0}
    for m, c, u in itertools.product((1, 2, 3), repeat=3):
        rec = mv.ModelRecord("m", "model", "owner", "use", m, c, u)
        share[rec.tier] += p[m - 1] * p[c - 1] * p[u - 1]
    return share


def intervals():
    rec = {1: (3, 3, 3), 2: (2, 2, 2), 3: (1, 1, 1)}
    return {t: mv.ModelRecord("m", "model", "owner", "use", *s).revalidate_years for t, s in rec.items()}


def inventory(n=MODELS, p=SCORE_P):
    s = tier_shares(p)
    c1, c2 = round(n * s[1]), round(n * s[2])
    return {1: c1, 2: c2, 3: n - c1 - c2}


def headcount(counts, change=CHANGE, full=FULL, interval=None):
    return fr.validator_headcount(counts, full, REVIEW, interval or intervals(), change, PRODUCTIVE)


def by_tier(counts):
    iv = intervals()
    return {t: fr.validation_hours({t: n}, FULL, REVIEW, iv, CHANGE) for t, n in counts.items()}


def curve(n=MODELS, shares=tuple(x / 100 for x in range(5, 45, 5))):
    base = inventory(n)
    out = []
    for s in shares:
        c1 = round(n * s)
        counts = {1: c1, 2: base[2], 3: n - base[2] - c1}
        out.append((s, headcount(counts)))
    return out


BOSS = {"CEO": None, "CRO": "CEO", "head of markets": "CEO", "head of model risk": "CRO",
        "validator A": "head of model risk",
        "head of risk analytics": "CRO", "risk developer": "head of risk analytics",
        "risk validator": "head of risk analytics", "validation team": "head of risk analytics",
        "head of quantitative analytics": "head of markets", "library developer": "head of quantitative analytics",
        "desk head": "head of markets", "desk strat": "desk head", "desk validator": "desk head"}
SENIOR = {"CRO", "head of markets"}
CASES = (("validator A", "library developer", "desk head"), ("validator A", "risk developer", None),
         ("validation team", "risk developer", None), ("desk validator", "desk strat", "desk head"))


def org_cases():
    return [(v, d, fr.independence(BOSS, SENIOR, v, d, o)) for v, d, o in CASES]


if __name__ == "__main__":
    for k, v in sorted(lca().items()):
        print(k, v.get("n"), v.get("employers"), v.get("p10"), v.get("p50"), v.get("p90"))
    for k, v in oews().items():
        print(k, v["occupation"], v["employment"], v["p10"], v["p50"], v["p90"])
    print("growth", growth())
    print("shares", tier_shares(), "intervals", intervals(), "inventory", inventory())
    inv = inventory()
    print("headcount", headcount(inv), by_tier(inv))
    for s, h in curve():
        print(s, round(h, 2))
    print(org_cases())


def sampled_headcount(draws=2000, seed=18, n=MODELS, p=SCORE_P):
    """Validators needed when the n models' scores are drawn at random (vectorised Book 6 tiering rule)."""
    import numpy as np

    rng = np.random.default_rng(seed)
    out = np.empty(draws)
    for k in range(draws):
        s = rng.choice((1, 2, 3), size=(n, 3), p=p)
        score = 2 * s[:, 0] + s[:, 1] + s[:, 2]
        c1, c2 = int((score >= 10).sum()), int(((score >= 7) & (score < 10)).sum())
        out[k] = headcount({1: c1, 2: c2, 3: n - c1 - c2})
    return out
