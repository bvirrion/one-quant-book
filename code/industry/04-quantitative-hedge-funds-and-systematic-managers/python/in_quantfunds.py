"""One Quant Book 17, chapter 4: quantitative hedge funds and systematic managers through Form ADV.

Reads the derived tables written by in_adv_derive.py from the SEC's January 2026 adviser file:
data/industry/adv_hedge_summary.csv (distribution statistics) and adv_named.csv (named managers' rows).
"""
import csv
import math
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[4]
DATA = ROOT / "data/industry"


def summary():
    with open(DATA / "adv_hedge_summary.csv") as f:
        return {r["stat"]: float(r["value"]) for r in csv.DictReader(f)}


def named():
    with open(DATA / "adv_named.csv") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for k in ("employees", "advisory", "raum_bn", "pf_gav_bn", "n_hedge"):
            r[k] = float(r[k])
        r["raum_per_employee_m"] = 1000 * r["raum_bn"] / r["employees"]
        r["gav_over_raum"] = r["pf_gav_bn"] / r["raum_bn"]
        r["advisory_share"] = r["advisory"] / r["employees"]
    return sorted(rows, key=lambda r: -r["raum_bn"])


def hist():
    with open(DATA / "adv_rpe_hist.csv") as f:
        return [{k: float(v) for k, v in r.items()} for r in csv.DictReader(f)]


def percentile_rank(rpe_m):
    """Share of hedge-fund advisers with 10+ employees below a RAUM per employee (in $m), from the histogram."""
    h = hist()
    tot = sum(r["advisers"] for r in h)
    lv = math.log10(rpe_m * 1e6)
    below = sum(r["advisers"] for r in h if r["log10_hi"] <= lv)
    part = next((r for r in h if r["log10_lo"] <= lv < r["log10_hi"]), None)
    if part:
        below += part["advisers"] * (lv - part["log10_lo"]) / (part["log10_hi"] - part["log10_lo"])
    return below / tot
