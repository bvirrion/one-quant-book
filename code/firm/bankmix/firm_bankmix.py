"""firm.bankmix -- banks' markets revenue by product line (build of One Quant Book 17, chapter 7).

Each bank reports its markets revenue in its own lines and currency. A row maps them to two standard lines, fixed
income (rates, credit, currencies, commodities: FICC) and equities (cash, derivatives, prime), with the bank's own
line names kept for the reader to check. Amounts are converted to one currency at the year's average rate. The measures
are the equities share of each bank's markets revenue, its change from one year to the next, and the share of the
group's equities revenue earned by the k most equity-heavy banks. Banks are ordered by mix, never by size or prestige.

API (stable):
    Row(bank, year, ficc, equities, currency, ledger, lines)
    load(path) -> list[Row] ; load_fx(path) -> {year: {"USD": 1, "EUR": usd_per_eur, "GBP": usd_per_gbp}}
    to_usd(row, fx) -> (ficc, equities) in USD
    equities_share(row) ; mix_table(rows, year) -> list of (bank, share) sorted by share
    mix_change(rows, bank, y0, y1) -> change of the equities share in percentage points
    top_k_equities_share(rows, fx, year, k) -> share of the year's equities revenue earned by the k most equity-heavy
"""
import csv
from dataclasses import dataclass


@dataclass(frozen=True)
class Row:
    bank: str
    year: int
    ficc: float
    equities: float
    currency: str
    ledger: str
    lines: str


def load(path):
    with open(path) as f:
        return [Row(r["bank"], int(r["year"]), float(r["ficc"]), float(r["equities"]), r["currency"], r["ledger"],
                    r["lines"]) for r in csv.DictReader(f)]


def load_fx(path):
    out = {}
    with open(path) as f:
        for r in csv.DictReader(f):
            ue, ge = float(r["usd_per_eur"]), float(r["gbp_per_eur"])
            out[int(r["year"])] = {"USD": 1.0, "EUR": ue, "GBP": ue / ge}
    return out


def to_usd(row, fx):
    k = fx[row.year][row.currency]
    return row.ficc * k, row.equities * k


def equities_share(row):
    tot = row.ficc + row.equities
    return row.equities / tot if tot else float("nan")


def mix_table(rows, year):
    return sorted(((r.bank, equities_share(r)) for r in rows if r.year == year), key=lambda x: -x[1])


def mix_change(rows, bank, y0, y1):
    s = {r.year: equities_share(r) for r in rows if r.bank == bank}
    return 100 * (s[y1] - s[y0])


def top_k_equities_share(rows, fx, year, k):
    ry = [r for r in rows if r.year == year]
    eq = {r.bank: to_usd(r, fx)[1] for r in ry}
    top = [b for b, _ in mix_table(ry, year)[:k]]
    return sum(eq[b] for b in top) / sum(eq.values())
