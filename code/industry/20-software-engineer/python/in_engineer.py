"""One Quant Book 17, chapter 20: the software engineer -- trading firms against banks, exchanges and technology.

Filings: chapter 19's code table (lca_soc.csv, SOC 15-1252 by employer kind) and this chapter's comparison
(lca_kind_gap.csv, derived from chapter 14's cache by in_lca_kind_gap_derive.py). Survey: software developers by
industry (oews_roles.csv), compared percentile by percentile with firm.roles.percentile_ratio. Scale: headcounts from
two 10-Ks and an annual report (constants below, ledger F1-F3).
"""
import csv
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/roles"))
import firm_roles as fr  # noqa: E402

DATA = ROOT / "data/industry"
LEVELS = ("I", "II", "III", "IV")
KINDS = ("systematic fund", "multi-manager platform", "market maker", "bank", "exchange")
INDUSTRIES = ("519200", "523000", "513200", "518200", "5220A1", "541500")
Q = ("p10", "p25", "p50", "p75", "p90")
VIRTU_EMPLOYEES = 1027          # 10-K for 2025: 'approximately 1,027 employees' at 13 February 2026
FLOW_FTE = 635                  # Annual Report 2025: FTEs at year-end 2025
MSFT_EMPLOYEES = 223_000        # 10-K for fiscal 2026: full-time employees at 30 June 2026
MSFT_RD = 77_000                # of whom in product research and development


def _read(name):
    with open(DATA / name) as f:
        return list(csv.DictReader(f))


def cells(fy=2025):
    out = {}
    for r in _read("lca_soc.csv"):
        if int(r["fy"]) == fy and r["soc"] == "15-1252" and r["level"] == "all" and r["scope"] in KINDS:
            c = {"n": int(r["n"]), "employers": int(r["employers"]), "suppressed": r["suppressed"] == "1"}
            if not c["suppressed"]:
                c.update({k: float(r[k]) for k in Q + ("lo50", "hi50")})
            out[r["scope"]] = c
    return out


def kind_gaps():
    return {(int(r["fy"]), r["versus"], r["level"]): {k: float(v) for k, v in r.items() if k not in ("fy", "versus",
                                                                                                "level")}
            for r in _read("lca_kind_gap.csv")}


def survey(occ="15-1252"):
    return {r["naics"]: r for r in _read("oews_roles.csv") if r["occ"] == occ}


def industry_ratios(base="523000"):
    s = survey()
    return {k: fr.percentile_ratio(s[base], s[k]) for k in INDUSTRIES if k != base}


def scale():
    return {"msft_per_virtu": MSFT_EMPLOYEES / VIRTU_EMPLOYEES, "rd_per_virtu": MSFT_RD / VIRTU_EMPLOYEES,
            "rd_share": MSFT_RD / MSFT_EMPLOYEES}


if __name__ == "__main__":
    for k, v in cells().items():
        print(k, v)
    for k, v in kind_gaps().items():
        print(k, round(v["ratio"], 3), round(v["ratio_lo"], 3), round(v["ratio_hi"], 3))
    for k, v in industry_ratios().items():
        print(k, {q: round(x, 3) for q, x in v.items()})
    print(scale())
