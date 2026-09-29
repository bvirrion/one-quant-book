"""firm.paydata -- public pay evidence, read and summarised with its caveats (build of One Quant Book 17, chapter 14).

Each public source of pay sees one slice: US labour condition applications (LCAs) the offered base salary of sponsored
positions; the government's occupational survey (OEWS) wage percentiles by industry and occupation, top-coded; filed
accounts staff cost per head, bonuses included; listed firms' pay-ratio disclosures the median employee's total pay;
bank remuneration reports the counts of high earners. The module streams the large LCA files without loading them,
classifies employers and roles by sourced rules, annualises offered wages, and computes percentile ranges with
bootstrap intervals, suppressing any cell built from fewer than ten filings. Every other source is converted into a
PayEvidence record that states what it measures, over whom, and its caveat, so that ranges from different sources are
compared only as what they are. Python with openpyxl (read-only mode) and NumPy.

API (stable):
    LCA_COLS
    read_lca(path, keep=None) -> iterator of dicts (streamed; `keep(row) -> bool` filters early)
    annualise(amount, unit) -> float | None
    Rule(pattern, label, kind, ledger); load_rules(path) -> list[Rule]; classify(name, rules) -> Rule | None
    ROLE_RULES; classify_role(title, soc) -> str | None
    MIN_CELL = 10
    cell(values, rng=None, n_boot=0) -> dict(n, p10, p25, p50, p75, p90, lo50, hi50) or dict(n, suppressed=True)
    PayEvidence(source, measure, population, year, lo, hi, unit, caveat)
"""
import csv
import re
from dataclasses import dataclass

import numpy as np

LCA_COLS = ("CASE_NUMBER", "CASE_STATUS", "VISA_CLASS", "JOB_TITLE", "SOC_CODE", "SOC_TITLE", "EMPLOYER_NAME",
            "NAICS_CODE", "WORKSITE_CITY", "WORKSITE_STATE", "WAGE_RATE_OF_PAY_FROM", "WAGE_RATE_OF_PAY_TO",
            "WAGE_UNIT_OF_PAY", "PREVAILING_WAGE", "PW_UNIT_OF_PAY", "PW_WAGE_LEVEL", "TOTAL_WORKER_POSITIONS",
            "BEGIN_DATE", "DECISION_DATE", "FULL_TIME_POSITION")
PER_YEAR = {"year": 1.0, "month": 12.0, "bi-weekly": 26.0, "week": 52.0, "hour": 2080.0}
MIN_CELL = 10


def read_lca(path, keep=None):
    """Stream an LCA disclosure workbook row by row, keeping LCA_COLS; the file is never loaded whole."""
    import openpyxl  # imported here so the rest of the module needs NumPy only

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        rows = wb.worksheets[0].iter_rows(values_only=True)
        header = [str(h).strip().upper() if h is not None else "" for h in next(rows)]
        idx = {c: header.index(c) for c in LCA_COLS if c in header}
        for r in rows:
            d = {c: r[i] for c, i in idx.items()}
            if keep is None or keep(d):
                yield d
    finally:
        wb.close()


def annualise(amount, unit):
    try:
        a = float(str(amount).replace(",", "").replace("$", ""))
    except (TypeError, ValueError):
        return None
    k = PER_YEAR.get(str(unit or "").strip().lower())
    return a * k if k and a > 0 else None


@dataclass(frozen=True)
class Rule:
    pattern: str
    label: str
    kind: str
    ledger: str


def load_rules(path):
    with open(path) as f:
        return [Rule(r["pattern"], r["label"], r["kind"], r["ledger"]) for r in csv.DictReader(f)]


def classify(name, rules):
    n = str(name or "").upper()
    for r in rules:
        if re.search(r.pattern, n):
            return r
    return None


ROLE_RULES = (  # first match wins; applied to the job title in upper case
    (r"PORTFOLIO MANAGER", "portfolio manager"),
    (r"QUANT\w*\s+(RESEARCH|RESEARCHER|ANALYST|STRATEGIST|MODEL)"
     r"|RESEARCH\w*\s+QUANT|QUANTITATIVE RESEARCH", "quant researcher"),
    (r"QUANT\w*\s+TRAD|ALGORITHMIC TRAD|\bTRADER\b|TRADING ANALYST", "trader"),
    (r"QUANT\w*\s+(DEVELOPER|ENGINEER|SOFTWARE)", "quant developer"),
    (r"MACHINE LEARNING|DATA SCIEN|DATA ENGINEER|\bML\b|\bAI\b", "ml and data"),
    (r"SOFTWARE|DEVELOPER|PROGRAMMER|SITE RELIABILITY|SYSTEMS ENGINEER"
     r"|INFRASTRUCTURE ENGINEER|\bSRE\b", "software engineer"),
    (r"\bRISK\b", "risk"),
)
SOC_ROLE = {"13-2099.01": "quant researcher", "15-2041": "quant researcher", "15-2051": "ml and data",
            "15-1252": "software engineer"}


def classify_role(title, soc):
    t = str(title or "").upper()
    for pat, role in ROLE_RULES:
        if re.search(pat, t):
            return role
    s = str(soc or "").strip()
    return SOC_ROLE.get(s) or SOC_ROLE.get(s[:7])


def cell(values, rng=None, n_boot=0):
    v = np.asarray([x for x in values if x is not None], dtype=float)
    n = len(v)
    if n < MIN_CELL:
        return {"n": n, "suppressed": True}
    q = np.percentile(v, [10, 25, 50, 75, 90])
    out = {"n": n, "p10": q[0], "p25": q[1], "p50": q[2], "p75": q[3], "p90": q[4]}
    if n_boot and rng is not None:
        meds = np.median(v[rng.integers(0, n, (n_boot, n))], axis=1)
        out["lo50"], out["hi50"] = (float(x) for x in np.percentile(meds, [2.5, 97.5]))
    return out


@dataclass(frozen=True)
class PayEvidence:
    source: str        # who publishes it
    measure: str       # what is measured: offered base, wage percentile, staff cost per head, median employee ...
    population: str    # over whom
    year: int
    lo: float
    hi: float
    unit: str
    caveat: str
