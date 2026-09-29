"""firm.posservice -- positions and P&L from executions, from two sources (build of One Quant Book 15, chapter 17).

Positions are event-sourced: the service stores executions, keyed by their execution identifier, and computes every
position by replaying them in time order through Book 1's exact position keeper (firm.pnl.Position: integer quantity
and cash, so that cash + quantity * mark - fees holds to the unit). Executions arrive from several sources -- the
order-entry session's execution reports and the venue's drop copy -- in any order and any number of times; an
execution is counted once whatever its source (idempotent on its identifier). Where the sources disagree about which
executions exist, the position is reported as pending until they agree. Busts remove an execution and corrections
replace its quantity or price; both are events, kept, so the position before and after is recoverable. Views: by trade
date and by settlement date. Marks: intraday from the feed, at the end of the day the official closing price; the
start-of-day position of the next date is the end-of-day position. Reconciliation compares positions with a clearing
statement and lists the breaks.

API (stable):
    Execution(exec_id, account, symbol, side, qty, price, ts, trade_date, settle_date, fee=0)
    PositionService(sources=('session', 'dropcopy'))
        .on_execution(source, execution) -> bool (False if already known) ; .on_bust(exec_id, ts)
        .on_correction(exec_id, ts, qty=None, price=None)
        .position(account, symbol, as_of=None, view='trade', date=None) -> firm.pnl.Position
        .status(account, symbol) -> 'agreed' | 'pending' ; .missing(source) -> exec ids the other sources have
        .pnl(account, symbol, mark, as_of=None) -> (total, realised, unrealised) in ledger units (1/10,000)
        .end_of_day(date, closes) -> {(account, symbol): (quantity, mark, total)} ; .start_of_day(date) -> same
    reconcile(service, statement {(account, symbol): quantity}, as_of=None) -> [(account, symbol, ours, theirs)]
"""
from __future__ import annotations

import pathlib
import sys
from dataclasses import dataclass, replace

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "pnl"))
from firm_pnl import Position  # noqa: E402


@dataclass(frozen=True)
class Execution:
    exec_id: str
    account: str
    symbol: str
    side: int                 # +1 buy, -1 sell
    qty: int
    price: int                # 1/10,000
    ts: int                   # nanoseconds
    trade_date: int           # days
    settle_date: int
    fee: int = 0


class PositionService:
    def __init__(self, sources=("session", "dropcopy")):
        self.sources = tuple(sources)
        self.execs: dict[str, Execution] = {}
        self.seen: dict[str, set] = {s: set() for s in self.sources}
        self.busted: dict[str, int] = {}
        self.corrections: list = []            # (ts, exec_id, qty, price)
        self.eod: dict[int, dict] = {}

    # -- events
    def on_execution(self, source: str, e: Execution) -> bool:
        self.seen[source].add(e.exec_id)
        if e.exec_id in self.execs:
            return False
        self.execs[e.exec_id] = e
        return True

    def on_bust(self, exec_id: str, ts: int) -> None:
        self.busted[exec_id] = ts

    def on_correction(self, exec_id: str, ts: int, qty: int | None = None,
                      price: int | None = None) -> None:
        self.corrections.append((ts, exec_id, qty, price))

    # -- state
    def _effective(self, as_of=None) -> list[Execution]:
        out = {}
        for k, e in self.execs.items():
            if as_of is not None and e.ts > as_of:
                continue
            if k in self.busted and (as_of is None or self.busted[k] <= as_of):
                continue
            out[k] = e
        for ts, k, q, p in sorted(self.corrections, key=lambda c: c[0]):
            if k in out and (as_of is None or ts <= as_of):
                e = out[k]
                out[k] = replace(e, qty=e.qty if q is None else q,
                                 price=e.price if p is None else p)
        return sorted(out.values(), key=lambda e: (e.ts, e.exec_id))

    def position(self, account, symbol, as_of=None, view="trade", date=None) -> Position:
        p = Position()
        for e in self._effective(as_of):
            if e.account != account or e.symbol != symbol:
                continue
            if view == "settlement" and (date is None or e.settle_date > date):
                continue
            p.on_fill(e.side, e.qty, e.price, e.fee)
        return p

    def status(self, account, symbol) -> str:
        mine = {k for k, e in self.execs.items()
                if e.account == account and e.symbol == symbol}
        ids = [self.seen[s] & mine for s in self.sources]
        return "agreed" if all(i == ids[0] for i in ids) else "pending"

    def missing(self, source: str) -> set:
        others = set().union(*(self.seen[s] for s in self.sources if s != source))
        return others - self.seen[source]

    def pnl(self, account, symbol, mark: int, as_of=None) -> tuple:
        p = self.position(account, symbol, as_of)
        return p.total(mark), p.realised, p.unrealised(mark)

    # -- day boundaries
    def end_of_day(self, date: int, closes: dict) -> dict:
        keys = {(e.account, e.symbol) for e in self.execs.values() if e.trade_date <= date}
        out = {}
        for a, s in sorted(keys):
            p = self.position(a, s)
            out[(a, s)] = (p.quantity, closes[s], p.total(closes[s]))
        self.eod[date] = out
        return out

    def start_of_day(self, date: int) -> dict:
        prev = max((d for d in self.eod if d < date), default=None)
        return dict(self.eod.get(prev, {}))


def reconcile(service: PositionService, statement: dict, as_of=None) -> list:
    keys = set(statement) | {(e.account, e.symbol) for e in service.execs.values()}
    breaks = []
    for a, s in sorted(keys):
        ours = service.position(a, s, as_of).quantity
        theirs = statement.get((a, s), 0)
        if ours != theirs:
            breaks.append((a, s, ours, theirs))
    return breaks
