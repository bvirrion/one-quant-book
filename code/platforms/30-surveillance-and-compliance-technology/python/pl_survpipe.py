"""Surveillance and compliance technology (One Quant Book 15, chapter 30).

A quarter (63 trading days) of account-days is drawn each day from Book 9's firm.surveil populations -- market makers,
quote refreshers, deep liquidity providers and directional traders for spoofing, ordinary accounts and index funds for
marking the close, ordinary accounts and multi-algorithm firms for wash trades -- with planted episodes arriving at
random. Each detector's threshold is calibrated on a separate quarter to a false-positive rate; the alerts go to a
team of two analysts who review eight alerts each a day, oldest first or highest score first. A message archive of 200
people is searched with a lexicon for conversations moving off channel, some of which leave no trace in it. A week of
equity trades is reported in a transaction-report format and validated and reconciled, first with a legacy generator
that has four planted faults, then with one that reads the event-sourced trade store.
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for c in ("survpipe", "surveil"):
    sys.path.insert(0, str(ROOT / "code/firm" / c))
import firm_surveil as SV  # noqa: E402
import firm_survpipe as S  # noqa: E402

DAYS, ANALYSTS, PER_ANALYST = 63, 2, 8
DETECTORS = {"spoofing": ("gap x cancel", SV.spoofing_days, SV.spoof_scores, 4),
             "marking the close": ("opposes settlement position", SV.close_days, SV.close_scores, 2),
             "wash trades": ("self-match share", SV.wash_days, SV.wash_scores, 2)}
DAILY = {"spoofing": (500, 300, 150, 200), "marking the close": (400, 150), "wash trades": (400, 100)}
EPISODES_PER_DAY = {"spoofing": 0.3, "marking the close": 0.2, "wash trades": 0.2}
FPRS = (0.002, 0.005, 0.01)


def day_population(det: str, day: int, seed: int = 30) -> dict:
    """One day's account-days for one detector, with planted episodes drawn at random."""
    rng = np.random.default_rng(seed * 1000 + day * 7 + list(DETECTORS).index(det))
    planted = int(rng.poisson(EPISODES_PER_DAY[det]))
    field_name = "counts" if det == "spoofing" else ("close_counts" if det == "marking the close" else "wash_counts")
    cfg = SV.SurveilConfig(seed=int(rng.integers(1 << 30)), **{field_name: (*DAILY[det], planted)})
    _score_name, make, score, _k = DETECTORS[det]
    d = make(cfg)
    d["score"] = score(d)[DETECTORS[det][0]]
    return d


def thresholds(fpr: float, calib_seed: int = 31) -> dict:
    """Each detector's threshold: the (1 - fpr) quantile of legitimate account-days in a calibration quarter."""
    out = {}
    for det in DETECTORS:
        legit = np.concatenate([(lambda d: d["score"][d["label"] == 0])(day_population(det, t, calib_seed))
                                for t in range(DAYS)])
        out[det] = float(np.quantile(legit, 1 - fpr))
    return out


def alerts(fpr: float, seed: int = 30) -> list[list]:
    h = thresholds(fpr)
    out, aid = [], 0
    for t in range(DAYS):
        today = []
        for det in DETECTORS:
            d = day_population(det, t, seed)
            for i in np.flatnonzero(d["score"] > h[det]):
                today.append(S.Alert(aid, t, f"{det[:4]}-{t}-{i}", det, float(d["score"][i]) / h[det],
                                     bool(d["label"][i])))
                aid += 1
        out.append(today)
    return out


def planted_total(seed: int = 30) -> int:
    return sum(int(day_population(det, t, seed)["label"].sum()) for det in DETECTORS for t in range(DAYS))


def queue_study(fpr: float, policy: str, analysts: int = ANALYSTS) -> dict:
    a = alerts(fpr)
    run = S.work_queue(a, analysts * PER_ANALYST, policy)
    reviewed_planted = [(al, day) for al, day in run.reviewed if al.planted]
    raised_planted = sum(al.planted for day in a for al in day)
    waits = [day - al.day for al, day in run.reviewed]
    return {"alerts_per_day": sum(map(len, a)) / DAYS, "backlog_end": run.backlog[-1], "backlog": run.backlog,
            "planted_raised": raised_planted, "planted_reviewed": len(reviewed_planted),
            "planted_within_5": sum(1 for al, day in reviewed_planted if day - al.day <= 5),
            "median_wait": float(np.median(waits)) if waits else 0.0}


# ------------------------------------------------------------ communications
BROAD = [r"whats\s?app", r"\bsignal\b", r"\btext me\b", r"\bmy cell\b", r"\boff the record\b", r"\bdon'?t put\b"]
NARROW = [r"(take|move) (this|it) to whats\s?app", r"\bsignal me\b", r"text me on my (personal|own)",
          r"call my cell", r"don'?t put this in the chat"]
PLAIN = ["the fill came in at the offer", "risk is flat into the close", "can you check the curve build",
         "new model in staging", "lunch at one?", "please review the pull request", "vol is bid again",
         "call when free", "positions reconciled", "the auction imbalance is large"]
TRIGGERS = ["signal decay on the momentum book looks fine", "the whatsapp outage made the news",
            "off the record, the demo went well", "text me the room number", "don't put sugar in mine"]
MOVES = ["let's take this to whatsapp", "text me on my personal phone", "call my cell, not the desk line",
         "don't put this in the chat", "signal me later", "ping me on the other app", "let's talk outside",
         "better on my own phone"]
TRIGGER_RATE = 0.002                               # benign messages that happen to use a lexicon word


def archive(people: int = 200, per_day: int = 20, n_conv: int = 40, trace_share: float = 0.6, seed: int = 30):
    """Messages of a quarter; `n_conv` conversations move off channel, of which `trace_share`
    leave a pointer in the archive and the rest leave nothing."""
    rng = np.random.default_rng(seed)
    msgs, mid = [], 0
    for t in range(DAYS):
        for _ in range(people * per_day):
            s = int(rng.integers(people))
            pool = TRIGGERS if rng.random() < TRIGGER_RATE else PLAIN
            msgs.append({"id": mid, "day": t, "sender": f"p{s:03d}", "conv": f"c{s:03d}-{t}",
                         "text": pool[int(rng.integers(len(pool)))], "planted": False})
            mid += 1
    moved = []
    for k in range(n_conv):
        t, s = int(rng.integers(DAYS)), int(rng.integers(people))
        conv = f"off{k:03d}"
        leaves_trace = rng.random() < trace_share
        if leaves_trace:
            msgs.append({"id": mid, "day": t, "sender": f"p{s:03d}", "conv": conv,
                         "text": MOVES[int(rng.integers(len(MOVES)))], "planted": True})
            mid += 1
        moved.append((conv, leaves_trace))
    return msgs, moved


def comms_study() -> dict:
    msgs, moved = archive()
    planted = {m["id"] for m in msgs if m["planted"]}
    out = {"messages": len(msgs), "planted_traces": len(planted), "conversations": len(moved),
           "invisible": sum(1 for _c, trace in moved if not trace)}
    for name, lex in (("broad", BROAD), ("narrow", NARROW)):
        hits = set(S.search(msgs, lex))
        out[name] = {"hits": len(hits), "true_hits": len(hits & planted)}
    return out


# ------------------------------------------------------------ transaction reports
FIRM = S.make_lei("FIRM00000000000000")
CLIENTS = [S.make_lei(f"CLNT{i:014d}") for i in range(5)]
BROKER_CCP = S.make_lei("CCPX00000000000000")
ISINS = {f"S{i:03d}": S.make_isin(f"XS{i:09d}") for i in range(50)}


def week_trades(n_per_day: int = 500, seed: int = 30) -> dict:
    """A week of equity executions for the firm's five clients, some amended later in the week."""
    rng = np.random.default_rng(seed)
    out = {}
    for d in range(5):
        for i in range(n_per_day):
            trn = f"T{d}{i:04d}"
            out[trn] = {"day": d, "isin": ISINS[f"S{int(rng.integers(50)):03d}"], "client": int(rng.integers(5)),
                        "side": int(rng.choice([1, -1])), "quantity": int(rng.integers(1, 100)) * 100,
                        "price": round(float(rng.uniform(20, 300)), 4), "sec": int(rng.integers(34200, 57600)),
                        "amended": bool(rng.random() < 0.02)}
    return out


def _report(trn, t, status="NEWT", qty=None) -> dict:
    buyer, seller = (CLIENTS[t["client"]], BROKER_CCP) if t["side"] == 1 else (BROKER_CCP, CLIENTS[t["client"]])
    h, m, s = t["sec"] // 3600, t["sec"] % 3600 // 60, t["sec"] % 60
    return {"status": status, "trn": trn, "executing_entity": FIRM, "buyer": buyer, "seller": seller,
            "isin": t["isin"], "venue": "XSIM", "quantity": qty if qty is not None else t["quantity"],
            "price": t["price"], "time": f"2026-09-{21 + t['day']:02d}T{h:02d}:{m:02d}:{s:02d}Z"}


def legacy_reports(trades: dict, seed: int = 30) -> list[dict]:
    """The legacy generator: copies each trade when it is booked, and has four faults -- a missing
    client LEI (1%), a mistyped ISIN (0.5%), amendments never reported (every amended trade keeps its
    first quantity) and a batch sent twice (0.3%)."""
    rng = np.random.default_rng(seed + 1)
    out = []
    for trn, t in trades.items():
        r = _report(trn, t, qty=t["quantity"] if not t["amended"] else t["quantity"] + 100)
        u = rng.random()
        if u < 0.01:
            r["buyer" if t["side"] == 1 else "seller"] = ""
        elif u < 0.015:
            r["isin"] = r["isin"][:-1] + str((int(r["isin"][-1]) + 1) % 10)
        out.append(r)
        if rng.random() < 0.003:
            out.append(dict(r))
    return out


def event_reports(trades: dict) -> list[dict]:
    """The fixed generator reads the event-sourced trade store: an amendment cancels the
    first report and sends a new one (CANC, then NEWT); identifiers from reference data."""
    out = []
    for trn, t in trades.items():
        if t["amended"]:
            out.append(_report(trn, t, qty=t["quantity"] + 100))       # as first booked
            out.append(_report(trn, t, status="CANC", qty=t["quantity"] + 100))
        out.append(_report(trn, t))
    return out


def report_study() -> dict:
    trades = week_trades()
    out = {}
    for name, reps in (("legacy", legacy_reports(trades)), ("event-sourced", event_reports(trades))):
        invalid = [r for r in reps if S.validate(r)]
        rec = S.reconcile([r for r in reps if not S.validate(r)], trades)
        out[name] = {"reports": len(reps), "invalid": len(invalid), "missing": len(rec["missing"]),
                     "extra": len(rec["extra"]), "mismatched": len(rec["mismatched"]),
                     "trades": len(trades)}
    return out
