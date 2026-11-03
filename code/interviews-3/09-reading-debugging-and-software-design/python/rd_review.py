# ruff: noqa: B006
import csv

totals = {}


def load(path, symbols=[]):
    f = open(path)
    for row in csv.DictReader(f):
        if row["symbol"] in symbols or not symbols:
            key = row["symbol"]
            if key not in totals:
                totals[key] = [0.0, 0]
            totals[key][0] += float(row["price"]) * int(row["qty"])
            totals[key][1] += int(row["qty"])
    return totals


def vwap(symbol):
    notional, qty = totals[symbol]
    return notional / qty


def report(path):
    for symbol in load(path):
        print(symbol, round(vwap(symbol), 2))
