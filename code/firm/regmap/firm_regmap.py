"""firm.regmap -- the regulatory map as data (analytical tool of One Quant Book 16, chapter 17; the chapter's subject
is law and has no build in the running-project sense). Information about where the rules are, not advice.

Rows: jurisdiction, activity, status (required | obligation | check), regime, category, reference, decision_days (the
statutory maximum period for a decision on an application, where the text sets one), as_of (YYYY-MM), source (the
ledger rows). `check` validates the schema: every row has a reference, an as-of month and a source. `query` returns
the rows a profile of (jurisdiction, activity) pairs touches; `regimes` counts the distinct regimes; `stale` lists rows
older than a number of months at a date; `longest_decision` gives the longest statutory period on the path.

API (stable):
    load(path) ; check(rows) -> list of problems ; query(rows, profile) ; regimes(rows)
    stale(rows, today, months) ; longest_decision(rows) ; ALGO_CHECKLIST
"""
import csv

FIELDS = ("jurisdiction", "activity", "status", "regime", "category", "reference", "decision_days", "as_of", "source")
STATUSES = ("required", "obligation", "check")

ALGO_CHECKLIST = (
    ("EU", "effective systems and risk controls: resilience, capacity, thresholds and limits, no erroneous orders",
     "Directive 2014/65/EU art. 17(1)"),
    ("EU", "business continuity arrangements; systems fully tested and monitored", "Directive 2014/65/EU art. 17(1)"),
    ("EU", "notify the competent authorities of engaging in algorithmic trading", "Directive 2014/65/EU art. 17(2)"),
    ("EU", "organisational requirements in detail",
     "Delegated Regulation (EU) 2017/589 (see One Quant Book 11 ch. 27)"),
    ("US", "pre-trade risk controls and supervisory procedures for market access",
     "Rule 15c3-5 (see One Quant Book 11 ch. 27)"),
)


def load(path):
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["decision_days"] = int(r["decision_days"]) if r["decision_days"] else None
    return rows


def check(rows):
    problems = []
    for i, r in enumerate(rows):
        missing = [k for k in FIELDS if k not in r]
        if missing:
            problems.append((i, "missing " + ", ".join(missing)))
            continue
        for k in ("reference", "as_of", "source"):
            if not r[k]:
                problems.append((i, f"empty {k}"))
        if r["status"] not in STATUSES:
            problems.append((i, f"bad status {r['status']}"))
        if len(r["as_of"]) != 7 or r["as_of"][4] != "-":
            problems.append((i, "as_of not YYYY-MM"))
    return problems


def query(rows, profile):
    """profile: iterable of (jurisdiction, activity)."""
    p = set(profile)
    return [r for r in rows if (r["jurisdiction"], r["activity"]) in p]


def regimes(rows):
    return sorted({(r["jurisdiction"], r["regime"]) for r in rows})


def _months(ym):
    y, m = ym.split("-")
    return int(y) * 12 + int(m) - 1


def stale(rows, today, months=12):
    return [r for r in rows if _months(today) - _months(r["as_of"]) > months]


def longest_decision(rows):
    ds = [(r["decision_days"], r["jurisdiction"], r["regime"]) for r in rows if r["decision_days"]]
    return max(ds) if ds else None
