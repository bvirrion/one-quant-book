"""firm.survpipe -- surveillance pipeline: features, alerts, cases, archive search, transaction reports (B15 ch. 30).

Order events become account-day features in Book 9's firm.surveil schema (orders placed, filled and cancelled by
size class, and large cancellations that follow a fill on the other side within a second); detectors score them and
alert above thresholds calibrated on a false-positive rate. Alerts become cases in a queue that a team of fixed size
works each day, oldest first or highest score first, so that the backlog and the age of what is reviewed can be
measured. A message archive is searched with a lexicon, and messages under a legal hold survive the retention job.
Transaction reports are generated from trades, validated field by field (LEI and ISIN with their check digits, a
segment MIC, positive quantity and price, an ISO 8601 time) and reconciled with the trades they report.

API (stable):
    features(events) -> {(account, day): {n_small, n_large, f_small, f_large, c_large, linked}}
        events: [(ts, account, day, order_id, side, size, action)], size 'small'|'large', action 'place'|'fill'|'cancel'
    Alert(aid, day, account, detector, score, planted=False) ; work_queue(alerts_by_day, per_day, policy) -> QueueRun
    search(messages, lexicon) -> [message ids] ; retention(messages, now, keep_days, holds) -> kept messages
    lei_ok(s) ; isin_ok(s) ; make_lei(p18) ; make_isin(p11) ; validate(report) -> [errors]
    reconcile(reports, trades) -> {missing, extra, mismatched}
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# ------------------------------------------------------------ features


def features(events) -> dict:
    out: dict = {}
    last_fill: dict = {}                            # (account, side) -> time of the last fill
    orders: dict = {}                               # order id -> (size, side)
    for ts, acct, day, oid, side, size, action in sorted(events):
        f = out.setdefault((acct, day), dict.fromkeys(("n_small", "n_large", "f_small", "f_large", "c_large",
                                                           "linked"), 0))
        if action == "place":
            orders[oid] = (size, side)
            f["n_" + size] += 1
        elif action == "fill":
            f["f_" + orders[oid][0]] += 1
            last_fill[(acct, side)] = ts
        elif action == "cancel" and orders[oid][0] == "large":
            f["c_large"] += 1
            other = "S" if orders[oid][1] == "B" else "B"
            if ts - last_fill.get((acct, other), -1e9) <= 1.0:
                f["linked"] += 1
    return out


# ------------------------------------------------------------ alerts and cases
@dataclass
class Alert:
    aid: int
    day: int
    account: str
    detector: str
    score: float
    planted: bool = False


@dataclass
class QueueRun:
    backlog: list = field(default_factory=list)      # open alerts at the end of each day
    reviewed: list = field(default_factory=list)     # (alert, day reviewed)


def work_queue(alerts_by_day: list, per_day: int, policy: str = "oldest") -> QueueRun:
    """Each day the day's alerts join the queue and the team reviews `per_day` of them:
    the oldest first, or the highest score first."""
    run, queue = QueueRun(), []
    for day, new in enumerate(alerts_by_day):
        queue.extend(new)
        if policy == "score":
            queue.sort(key=lambda a: (-a.score, a.day, a.aid))
        else:
            queue.sort(key=lambda a: (a.day, a.aid))
        take, queue = queue[:per_day], queue[per_day:]
        run.reviewed += [(a, day) for a in take]
        run.backlog.append(len(queue))
    return run


# ------------------------------------------------------------ communications archive
def search(messages, lexicon) -> list:
    """Ids of messages matching any lexicon pattern (case-insensitive regular expressions)."""
    rx = re.compile("|".join(f"(?:{p})" for p in lexicon), re.IGNORECASE)
    return [m["id"] for m in messages if rx.search(m["text"])]


def retention(messages, now: int, keep_days: int, holds: set) -> list:
    """What the retention job keeps: messages younger than `keep_days`, and any message whose
    sender or conversation is under a legal hold."""
    return [m for m in messages if now - m["day"] < keep_days or m["sender"] in holds or m["conv"] in holds]


# ------------------------------------------------------------ transaction reports
def _alnum_value(s: str) -> str:
    return "".join(str(int(c, 36)) for c in s)


def lei_ok(s: str) -> bool:
    """20 characters, A-Z and 0-9, the last two check digits by ISO 7064 MOD 97-10."""
    return bool(re.fullmatch(r"[A-Z0-9]{18}[0-9]{2}", s or "")) and int(_alnum_value(s)) % 97 == 1


def isin_ok(s: str) -> bool:
    """Two letters, nine alphanumerics, one check digit (Luhn over the digits of the letters' values)."""
    if not re.fullmatch(r"[A-Z]{2}[A-Z0-9]{9}[0-9]", s or ""):
        return False
    digits = [int(d) for d in _alnum_value(s[:-1])]
    total = 0
    for i, d in enumerate(reversed(digits)):
        d = d * 2 if i % 2 == 0 else d
        total += d - 9 if d > 9 else d
    return (10 - total % 10) % 10 == int(s[-1])


TIME = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,9})?Z")


def validate(r: dict) -> list[str]:
    errs = []
    if r.get("status") not in ("NEWT", "CANC"):
        errs.append("status")
    for f in ("executing_entity", "buyer", "seller"):
        if not lei_ok(r.get(f, "")):
            errs.append(f)
    if not isin_ok(r.get("isin", "")):
        errs.append("isin")
    if not re.fullmatch(r"[A-Z0-9]{4}", r.get("venue", "")):
        errs.append("venue")
    if not (isinstance(r.get("quantity"), int | float) and r["quantity"] > 0):
        errs.append("quantity")
    if not (isinstance(r.get("price"), int | float) and r["price"] > 0):
        errs.append("price")
    if not TIME.fullmatch(r.get("time", "")):
        errs.append("time")
    return errs


def reconcile(reports, trades) -> dict:
    """Net each reference's reports (a CANC removes the report it cancels) and compare with
    the firm's trades by reference: missing, extra, and mismatched quantity or price."""
    live: dict = {}
    for r in reports:
        if r["status"] == "CANC":
            live.pop(r["trn"], None)
        elif r["trn"] in live:
            live[r["trn"] + "#dup"] = r
        else:
            live[r["trn"]] = r
    out = {"missing": [], "extra": [], "mismatched": []}
    for trn, t in trades.items():
        r = live.get(trn)
        if r is None:
            out["missing"].append(trn)
        elif r["quantity"] != t["quantity"] or abs(r["price"] - t["price"]) > 1e-9:
            out["mismatched"].append(trn)
    out["extra"] = sorted(k for k in live if k not in trades)
    return out


def make_lei(prefix18: str) -> str:
    """An LEI from its first 18 characters, with the check digits that make it valid."""
    return f"{prefix18}{98 - int(_alnum_value(prefix18 + '00')) % 97:02d}"


def make_isin(prefix11: str) -> str:
    """An ISIN from its first 11 characters, with its check digit."""
    for d in range(10):
        if isin_ok(prefix11 + str(d)):
            return prefix11 + str(d)
    raise ValueError(prefix11)
