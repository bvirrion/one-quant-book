"""One Quant Book 17, chapter 19: the quant developer -- one title, three jobs, several occupation codes.

Pay and codes: chapter 14's LCA tables (lca_ranges.csv, lca_titles.csv) and this chapter's code tables (lca_soc.csv,
lca_soc_gap.csv, derived from chapter 14's cache by in_lca_soc_derive.py); the survey's software developers
(oews_roles.csv). Titles: firm.roles.normalise_title on an ILLUSTRATIVE list of advertised titles (not data).
"""
import csv
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/roles"))
import firm_roles as fr  # noqa: E402

DATA = ROOT / "data/industry"
LEVELS = ("I", "II", "III", "IV")
FAMILIES = ("quant researcher", "quant developer", "software engineer", "ml and data")
TITLES = ("Quantitative Developer", "Sr. Quant Developer - Equities", "VP, Quant Dev", "Quant Dev L3",
          "Quantitative Developer II", "C++ Developer, Trading Systems", "Low Latency Software Engineer",
          "Research Engineer - Machine Learning", "Quantitative Research Engineer", "Software Engineer (Low Latency)",
          "Lead SWE / C++", "Associate Quantitative Analyst")


def _read(name):
    with open(DATA / name) as f:
        return list(csv.DictReader(f))


def family_totals(fy=2025):
    tot = {}
    for r in _read("lca_ranges.csv"):
        if int(r["fy"]) == fy and r["level"] == "all" and r["role"] in FAMILIES:
            tot[r["role"]] = tot.get(r["role"], 0) + int(r["n"])
    return tot


def soc_mix(fy=2025):
    """Per family: the FY2025 count of each SOC code with ten or more filings, and the rest as 'other'."""
    tot = family_totals(fy)
    mix = {f: {} for f in FAMILIES}
    for r in _read("lca_titles.csv"):
        if r["role"] in mix:
            mix[r["role"]][r["soc"]] = int(r["n"])
    for f in FAMILIES:
        mix[f]["other"] = tot[f] - sum(mix[f].values())
    return mix, tot


def soc_cells(fy=2025, scope="all finance"):
    out = {}
    for r in _read("lca_soc.csv"):
        if int(r["fy"]) == fy and r["scope"] == scope:
            c = {"n": int(r["n"]), "employers": int(r["employers"]), "suppressed": r["suppressed"] == "1"}
            if not c["suppressed"]:
                c.update({k: float(r[k]) for k in ("p10", "p25", "p50", "p75", "p90", "lo50", "hi50")})
            out[(r["soc"], r["level"])] = c
    return out


def gaps():
    return {(int(r["fy"]), r["level"]): {k: float(v) for k, v in r.items() if k not in ("fy", "level")}
            for r in _read("lca_soc_gap.csv")}


def level_mix(fy=2025, codes=("15-1252", "13-2099.01")):
    c = soc_cells(fy)
    out = {}
    for s in codes:
        n = [c[(s, lv)]["n"] for lv in LEVELS]
        out[s] = [x / sum(n) for x in n]
    return out


def reweighted_gap(fy=2025):
    """Software developers' median-by-level averaged with the quant analysts' level shares, minus the analysts'
    overall median: the gap with the level mix held at the analysts'."""
    c, mix = soc_cells(fy), level_mix(fy)["13-2099.01"]
    dev = sum(w * c[("15-1252", lv)]["p50"] for w, lv in zip(mix, LEVELS, strict=True))
    qa = sum(w * c[("13-2099.01", lv)]["p50"] for w, lv in zip(mix, LEVELS, strict=True))
    return dev - qa


def quantdev_cells():
    rows = [r for r in _read("lca_ranges.csv") if r["role"] == "quant developer" and r["level"] == "all"]
    return {(int(r["fy"]), r["kind"]): (int(r["n"]), int(r["employers"]), r["suppressed"] == "1") for r in rows}


def survey(occ="15-1252"):
    return {r["naics"]: r for r in _read("oews_roles.csv") if r["occ"] == occ}


def titles():
    return [(t, *fr.normalise_title(t)) for t in TITLES]


if __name__ == "__main__":
    print(soc_mix())
    for k, v in sorted(soc_cells().items()):
        print(k, v.get("n"), v.get("employers"), v.get("p50"))
    print(gaps())
    print(level_mix(), reweighted_gap())
    print(quantdev_cells())
    for t in titles():
        print(t)
    s = survey()
    for k in ("523000", "5220A1", "513200", "52"):
        print(k, s[k]["employment"], s[k]["p10"], s[k]["p50"], s[k]["p90"])
