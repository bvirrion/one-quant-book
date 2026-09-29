"""firm.compliance -- restricted and watch lists through time, pre-clearance of personal trades, an insider-list
register with wall-crossings, and the capacity of an alert-triage queue on firm.surveil's detectors (build of One
Quant Book 16, chapter 16).

Lists are intervals: (symbol, first day, last day). A personal trade request (employee, symbol, side, day) is refused,
with the first reason that applies, if the symbol is on the restricted list, on the watch list, if the firm traded
it within the blackout window before the request, if it would sell a position held for less than the minimum
holding period, or if the employee is an insider for it; otherwise it is approved. A wall-crossing puts a person on
the insider list for a project's symbol from the day they are crossed until the project is cleansed.

Triage: alerts are the account-days whose score exceeds the quantile giving a chosen alert rate. Analysts can review
`capacity` alerts; in arrival order, the expected true cases found are the true alerts times the reviewed share; in
score order, the reviewed alerts are the highest-scored.

API (stable):
    Lists(restricted, watch) ; Lists.on(kind, symbol, day)
    Rules(blackout_days, holding_days) ; preclear(req, lists, firm_trades, holdings, insiders, rules) -> (ok, reason)
    Register: cross(person, project, symbol, day) ; cleanse(project, day) ; insiders(symbol, day)
    triage(score, label, alert_rate, capacity, order) -> dict ; best_rate(score, label, capacity, rates, order)
"""
from dataclasses import dataclass, field

import numpy as np


@dataclass
class Lists:
    restricted: list = field(default_factory=list)     # (symbol, first, last)
    watch: list = field(default_factory=list)

    def on(self, kind, symbol, day):
        return any(s == symbol and a <= day <= b for s, a, b in getattr(self, kind))


@dataclass(frozen=True)
class Rules:
    blackout_days: int = 2
    holding_days: int = 30


def preclear(req, lists, firm_trades, holdings, insiders=frozenset(), rules=None):
    """req: (employee, symbol, side, day), side +1 buy / -1 sell; firm_trades: {symbol: sorted days};
    holdings: {(employee, symbol): day bought}; insiders: set of (employee, symbol) on the insider list that day."""
    rules = rules or Rules()
    emp, sym, side, day = req
    if lists.on("restricted", sym, day):
        return False, "restricted list"
    if lists.on("watch", sym, day):
        return False, "watch list"
    if (emp, sym) in insiders:
        return False, "insider"
    if any(day - rules.blackout_days <= t <= day for t in firm_trades.get(sym, ())):
        return False, "firm traded recently"
    bought = holdings.get((emp, sym))
    if side < 0 and bought is not None and day - bought < rules.holding_days:
        return False, "holding period"
    return True, "approved"


@dataclass
class Register:
    entries: list = field(default_factory=list)          # [person, project, symbol, crossed, cleansed or None]

    def cross(self, person, project, symbol, day):
        self.entries.append([person, project, symbol, day, None])

    def cleanse(self, project, day):
        for e in self.entries:
            if e[1] == project and e[4] is None:
                e[4] = day

    def insiders(self, symbol, day):
        return {e[0] for e in self.entries if e[2] == symbol and e[3] <= day and (e[4] is None or day < e[4])}


def triage(score, label, alert_rate, capacity, order="arrival"):
    score, label = np.asarray(score, float), np.asarray(label)
    thr = np.quantile(score, 1 - alert_rate)
    alerted = np.nonzero(score > thr)[0]
    a, tp = len(alerted), int(label[alerted].sum())
    reviewed = min(a, capacity)
    if order == "score":
        top = alerted[np.argsort(-score[alerted], kind="stable")[:reviewed]]
        found = float(label[top].sum())
    else:
        found = tp * reviewed / a if a else 0.0
    return {"threshold": float(thr), "alerts": a, "true_alerts": tp, "reviewed": reviewed, "found": found,
            "missed": int(label.sum()) - found}


def best_rate(score, label, capacity, rates, order="arrival"):
    res = {r: triage(score, label, r, capacity, order)["found"] for r in rates}
    return max(res, key=res.get), res
