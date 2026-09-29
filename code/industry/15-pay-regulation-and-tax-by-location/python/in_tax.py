"""One Quant Book 17, chapter 15: what a pay package is worth after tax in eight places, with firm.aftertax.

Packages are stated in US dollars and converted to each local currency at the ECB's 2025 average rates; a single
employee with no other income, standard deductions only. Amsterdam is shown with and without the expat scheme.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/aftertax"))
import firm_aftertax as at  # noqa: E402

P = at.load(ROOT / "data/industry/tax_2026.csv", ROOT / "data/industry/ch_federal_tax_2026.csv")
GRID = (150e3, 200e3, 300e3, 500e3, 750e3, 1e6, 1.5e6, 2e6, 3e6)
NAMES = {"london": "London", "new_york": "New York", "chicago": "Chicago", "amsterdam": "Amsterdam",
         "zurich": "Zurich", "singapore": "Singapore", "hong_kong": "Hong Kong", "dubai": "Dubai"}
PACKAGE = 1e6  # 30% base and 70% bonus in the problem; the split does not change the year's tax here


def curve():
    out = {loc: [at.net_usd(P, loc, g)["avg_rate"] for g in GRID] for loc in at.LOCATIONS}
    out["amsterdam expat"] = [at.net_usd(P, "amsterdam", g, expat=True)["avg_rate"] for g in GRID]
    return out


MGRID = tuple(float(g) for g in range(150_000, 3_000_001, 25_000))


def marginal_curve():
    return {loc: [at.marginal(P, loc, g, step=5000.0) for g in MGRID] for loc in at.LOCATIONS}


def million():
    """Net pay from the one-million package in each place, and the marginal rate on its last dollar of bonus."""
    rows = {}
    for loc in at.LOCATIONS:
        r = at.net_usd(P, loc, PACKAGE)
        rows[loc] = dict(net=r["net"], tax=r["tax"], social=r["social"], avg=r["avg_rate"],
                         marginal=at.marginal(P, loc, PACKAGE, step=1000.0), local=PACKAGE * at.local_per_usd(P, loc))
    ex = at.net_usd(P, "amsterdam", PACKAGE, expat=True)
    rows["amsterdam expat"] = dict(net=ex["net"], tax=ex["tax"], social=ex["social"], avg=ex["avg_rate"],
                                   marginal=at.marginal(P, "amsterdam", PACKAGE, step=1000.0, expat=True),
                                   local=PACKAGE * at.local_per_usd(P, "amsterdam"))
    return rows


def spread(include_expat=False):
    m = million()
    keys = [k for k in m if include_expat or k != "amsterdam expat"]
    hi = max(keys, key=lambda k: m[k]["net"])
    lo = min(keys, key=lambda k: m[k]["net"])
    return dict(hi=hi, lo=lo, ratio=m[hi]["net"] / m[lo]["net"])


if __name__ == "__main__":
    for k, v in million().items():
        print(k, {a: round(b, 3) if abs(b) < 10 else round(b) for a, b in v.items()})
    print(spread(), spread(True))
