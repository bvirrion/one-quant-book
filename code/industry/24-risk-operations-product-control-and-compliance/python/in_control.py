"""One Quant Book 17, chapter 24: control functions -- base pay against the front office, and pay mix.

Base pay: lca_control_gap.csv (risk titles against trader and quantitative-researcher titles, derived from chapter
14's cache by in_lca_control_derive.py). Pay mix: chapter 14's eba_high_earners.csv through firm.roles.fixed_share and
mix_gap. Survey: oews_roles.csv for the functions' occupations in the securities industry.
"""
import csv
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/roles"))
import firm_roles as fr  # noqa: E402

DATA = ROOT / "data/industry"
LEVELS = ("I", "II", "III", "IV")
OCCS = (("43-4011", "brokerage clerks"), ("13-1041", "compliance officers"), ("13-2011", "accountants and auditors"),
        ("13-2051", "financial and investment analysts"), ("13-2054", "financial risk specialists"))


def _read(name):
    with open(DATA / name) as f:
        return list(csv.DictReader(f))


def ratios():
    return {(int(r["fy"]), r["scope"], r["level"]): {k: float(v) for k, v in r.items() if k not in ("fy", "scope",
                                                                                                "level")}
            for r in _read("lca_control_gap.csv")}


def eba(institutions="credit institutions"):
    return {r["business_area"]: (int(float(r["high_earners"])), float(r["variable_to_fixed"]))
            for r in _read("eba_high_earners.csv") if r["institutions"] == institutions and r["variable_to_fixed"]}


def mix():
    e = eba()
    return fr.mix_gap(e["Independent control functions"][1], e["Investment banking"][1])


def survey(naics="523000"):
    return {r["occ"]: r for r in _read("oews_roles.csv") if r["naics"] == naics and r["occ"] in dict(OCCS)}


if __name__ == "__main__":
    for k, v in ratios().items():
        print(k, round(v["ratio"], 3), round(v["ratio_lo"], 3), round(v["ratio_hi"], 3), v["diff"])
    print(eba())
    print(mix())
    for k, v in survey().items():
        print(k, v["occupation"], v["employment"], v["p50"])
