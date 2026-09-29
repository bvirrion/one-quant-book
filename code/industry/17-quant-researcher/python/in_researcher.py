"""One Quant Book 17, chapter 17: the quantitative researcher -- pay evidence and feedback speed.

Pay: chapter 14's tables. Feedback: firm.roles, with Lo's (2002) standard error of the Sharpe ratio (IID returns) and
the fundamental law (Grinold 1989) with ILLUSTRATIVE skill (information coefficient 0.02 per bet) and breadth (50
independent bets per rebalance).
"""
import csv
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/roles"))
import firm_roles as fr  # noqa: E402

DATA = ROOT / "data/industry"
KINDS = ("systematic fund", "multi-manager platform", "market maker", "bank", "exchange")
HORIZONS = {"minute": 252 * 390, "hour": 252 * 6.5, "day": 252, "week": 52, "month": 12, "quarter": 4}
IC, BREADTH = 0.02, 50
NAMED = (("day", 2.0), ("week", 1.0), ("month", 0.5))


def pay():
    with open(DATA / "lca_ranges.csv") as f:
        rows = list(csv.DictReader(f))
    return {lvl: fr.lca_cells(rows, "quant researcher", 2025, lvl) for lvl in ("all", "I", "II", "III", "IV")}


def titles():
    with open(DATA / "lca_titles.csv") as f:
        return {r["soc"]: int(r["n"]) for r in csv.DictReader(f) if r["role"] == "quant researcher"}


def named():
    return {h: (sr, fr.years_to_significance(sr, HORIZONS[h]), fr.periods_to_significance(sr, HORIZONS[h]))
            for h, sr in NAMED}


def law_curve():
    out = []
    for h, ppy in HORIZONS.items():
        sr = fr.fundamental_law_sr(IC, BREADTH, ppy)
        out.append((h, ppy, sr, fr.years_to_significance(sr, ppy), fr.periods_to_significance(sr, ppy)))
    return out


if __name__ == "__main__":
    print(named())
    for r in law_curve():
        print(r)
    print(titles())
