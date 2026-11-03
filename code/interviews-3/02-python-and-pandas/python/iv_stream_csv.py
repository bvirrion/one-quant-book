import csv
from collections import defaultdict


def rows(path):
    with open(path, newline="") as f:
        yield from csv.DictReader(f)


def notional_by_symbol(records):
    totals = defaultdict(int)
    for r in records:
        totals[r["symbol"]] += int(r["price_ticks"]) * int(r["qty"])
    return dict(totals)
