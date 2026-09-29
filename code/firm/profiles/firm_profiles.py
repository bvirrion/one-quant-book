"""firm.profiles -- a sourced-fact store for firm profiles (build of One Quant Book 17, chapter 2).

A profile is a set of facts. Each fact carries a field (founded, employees, offices, revenue, products ...), a
range [low, high] in a unit (a point value is a range of width zero; an open bound is None, as in "more than
3,000 employees"), a text value for descriptive fields, the date it describes, its scope (the whole firm, or one
legal entity of it) and the ledger row that sources it. Nothing enters a profile without a ledger row and a date.

API (stable):
    Fact(firm, field, low, high, unit, as_of, scope, ledger, text="")
    load_facts(path) -> list[Fact]
    problems(facts, ledger_ids, today, max_age_days=None) -> list[str]   empty when every fact is admissible
    widen(value, rounding) -> (low, high)        a figure the source rounded to `rounding`, as a range
    coverage(facts, fields, scope="firm") -> dict[firm, set[field]]
    gap(facts, fields, listed) -> dict           fields filled by listed and by private firms
    table(facts, fields) -> list[list[str]]      one row per firm, one printable cell per field
"""
import csv
import datetime as dt
import math
from dataclasses import dataclass
from statistics import median


@dataclass(frozen=True)
class Fact:
    firm: str
    field: str
    low: float | None
    high: float | None
    unit: str
    as_of: str
    scope: str
    ledger: str
    text: str = ""


def _num(x):
    x = (x or "").strip()
    return float(x) if x else None


def load_facts(path):
    with open(path) as f:
        return [Fact(r["firm"], r["field"], _num(r["low"]), _num(r["high"]), r["unit"], r["as_of"], r["scope"],
                     r["ledger"], r.get("text", "")) for r in csv.DictReader(f)]


def _date(s):
    parts = [int(p) for p in s.split("-")]
    return dt.date(parts[0], parts[1] if len(parts) > 1 else 12, parts[2] if len(parts) > 2 else 28)


def problems(facts, ledger_ids, today, max_age_days=None):
    """Reasons a fact may not be printed: no ledger row, no date, an inverted range, no value, stale."""
    out = []
    for f in facts:
        tag = f"{f.firm}/{f.field}"
        if f.ledger not in ledger_ids:
            out.append(f"{tag}: ledger row {f.ledger!r} missing")
        if not f.as_of:
            out.append(f"{tag}: no date")
        elif max_age_days is not None and (today - _date(f.as_of)).days > max_age_days:
            out.append(f"{tag}: older than {max_age_days} days")
        if f.low is not None and f.high is not None and f.low > f.high:
            out.append(f"{tag}: low above high")
        if f.low is None and f.high is None and not f.text:
            out.append(f"{tag}: no value")
        if f.scope not in ("firm", "entity"):
            out.append(f"{tag}: scope must be firm or entity")
    return out


def widen(value, rounding):
    """A figure the source gives rounded to `rounding` ("300 employees", rounding 100) is the range it rounds."""
    h = rounding / 2
    return value - h, value + h


def coverage(facts, fields, scope="firm"):
    out = {}
    for f in facts:
        out.setdefault(f.firm, set())
        if f.field in fields and f.scope == scope:
            out[f.firm].add(f.field)
    return out


def gap(facts, fields, listed):
    cov = coverage(facts, fields)
    lst = [len(v) for k, v in cov.items() if k in listed]
    prv = [len(v) for k, v in cov.items() if k not in listed]
    return dict(fields=len(fields), listed=lst, private=sorted(prv), private_median=median(prv) if prv else math.nan,
                revenue_private=sum("revenue" in v for k, v in cov.items() if k not in listed))


def _cell(f):
    if f.unit == "text":
        return f.text
    if f.unit == "year":
        return f"{f.low:.0f}"
    if f.low is not None and f.high is not None:
        v = f"{f.low:,.0f}" if f.low == f.high else f"{f.low:,.0f}-{f.high:,.0f}"
    elif f.low is not None:
        v = f"{f.low:,.0f}+"
    else:
        v = f"up to {f.high:,.0f}"
    return f"{v} ({f.as_of})"


def table(facts, fields):
    firms = sorted({f.firm for f in facts})
    rows = []
    for firm in firms:
        cells = []
        for fld in fields:
            fs = [f for f in facts if f.firm == firm and f.field == fld and f.scope == "firm"]
            cells.append(_cell(fs[0]) if fs else "")
        rows.append([firm] + cells)
    return rows
