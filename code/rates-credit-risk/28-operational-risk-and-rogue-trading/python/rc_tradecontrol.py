"""Chapter 28 of Book 6: operational risk and rogue trading. A synthetic blotter of 2,000 genuine trades with
realistic noise and 60 trades of a concealment scheme (late bookings, unmatched internal trades, deferred
settlement, off-market prices, cancellations around reporting dates); the five surveillance rules, their hit
and false-alarm rates alone and combined; the Basel standardised operational-risk capital; and the
arithmetic of the January 2008 unwind (EUR 6.4bn on a EUR 49bn position)."""
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/tradecontrol"))
from firm_tradecontrol import AuditLog, Trade, evaluate, run_rules, trade_event  # noqa: E402

HOURS = 24 * 250
REPORTING = [24.0 * d for d in range(21, 250, 21)]          # a reporting date every 21 days


def blotter(n_clean: int = 2000, n_fraud: int = 60, seed: int = 4) -> list[Trade]:
    rng = np.random.default_rng(seed)
    out = []
    for i in range(n_clean):
        ex = float(rng.uniform(0, HOURS))
        late = rng.random() < 0.04
        internal = rng.random() < 0.10
        cancel = rng.random() < 0.05
        out.append(Trade(
            trade_id=f"C{i}", trader=f"T{i % 20}", executed=ex,
            booked=ex + (float(rng.uniform(5, 30)) if late else float(rng.uniform(0, 1))),
            price=100.0 + float(rng.normal(0, 0.03 if rng.random() > 0.01 else 0.5)), mid=100.0, spread=0.05,
            counterparty="INT:B2" if internal else "EXT:X",
            mirror=(f"C{i}" if internal and rng.random() > 0.02 else None),
            settle_days=int(rng.choice([2, 2, 2, 2, 3, 35])) if rng.random() < 0.05 else 2,
            status="cancelled" if cancel else "live", status_time=float(rng.uniform(0, HOURS)) if cancel else None))
    for i in range(n_fraud):
        ex = float(rng.uniform(0, HOURS))
        internal = rng.random() < 0.5
        cancel = rng.random() < 0.5
        out.append(Trade(
            trade_id=f"F{i}", trader="T7", executed=ex,
            booked=ex + (float(rng.uniform(6, 72)) if rng.random() < 0.4 else float(rng.uniform(0, 1))),
            price=100.0 + (float(rng.normal(0, 0.5)) if rng.random() < 0.3 else float(rng.normal(0, 0.03))),
            mid=100.0, spread=0.05, counterparty="INT:B9" if internal else "EXT:Y", mirror=None,
            settle_days=int(rng.integers(40, 120)) if rng.random() < 0.3 else 2,
            status="amended" if cancel else "live",
            status_time=(float(rng.choice(REPORTING)) + float(rng.uniform(-24, 24))) if cancel else None,
            fraud=True))
    return out


def surveillance() -> dict:
    b = blotter()
    rules = run_rules(b, REPORTING)
    return {"one": evaluate(b, rules, 1), "two": evaluate(b, rules, 2), "n": len(b),
            "fraud": sum(t.fraud for t in b)}


def audit_demo() -> dict:
    b = blotter()[:50]
    log = AuditLog()
    for t in b:
        log.append(trade_event(t))
    ok = log.verify()
    log.entries[10]["event"]["price"] = 99.0
    return {"before": ok, "after_edit": log.verify()}


# ---- operational-risk capital (Basel standardised approach) ------------------------------------------------
def bic(bi: float) -> float:
    """Business indicator component (EUR bn): marginal 12% up to 1, 15% from 1 to 30, 18% above."""
    return 0.12 * min(bi, 1.0) + 0.15 * max(0.0, min(bi, 30.0) - 1.0) + 0.18 * max(0.0, bi - 30.0)


def ilm(lc: float, b: float) -> float:
    return math.log(math.e - 1.0 + (lc / b) ** 0.8)


def op_capital(bi: float, avg_loss: float) -> dict:
    b = bic(bi)
    lc = 15.0 * avg_loss
    m = ilm(lc, b)
    return {"bic": b, "lc": lc, "ilm": m, "capital": b * m}


def unwind(loss: float = 6.4, position: float = 49.0) -> float:
    """Average adverse move implied by a loss on a position of a given size."""
    return loss / position
