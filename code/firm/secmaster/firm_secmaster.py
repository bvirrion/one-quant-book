"""firm.secmaster -- the security master and universes through time (build of One Quant Book 7, ch. 4).

Every listing gets a permanent identifier (an integer) at birth; tickers are attributes with date ranges,
changed and reused over time. Queries are as of a date: which listing held a ticker, which ticker a
listing had, what was listed, how a listing ended. Universes are built on a rebalance calendar from a
liquidity measure known at each date, with an entry rank and a wider exit rank (a buffer) so that names
near the boundary do not flicker in and out. Dates are any comparable values (ints, ISO strings, dates).

API (stable):
    SecurityMaster()
    .list(pid, ticker, date, issuer=None)            a new listing
    .rename(pid, ticker, date)                        ticker change from `date` on
    .delist(pid, date, reason, ret=None)              last trading date, reason ("merger", "performance", ...)
                                                      and the delisting return if known
    .resolve(ticker, date)                            permanent id holding the ticker on `date`, or None
    .ticker(pid, date)                                ticker of the listing on `date`, or None
    .listed(date)                                     set of permanent ids listed on `date`
    .spans(pid)                                       [(start, end or None, ticker), ...]
    .delisting(pid)                                   (date, reason, ret) or None
    .reused()                                         tickers held by more than one listing, with holders
    buffered_universe(dates, scores, n, exit_rank)    {date: set of ids}; scores(date) -> {id: liquidity}
    churn(universe)                                   average share of members replaced per rebalance
"""
from __future__ import annotations

import bisect
from collections import defaultdict


class SecurityMaster:
    def __init__(self):
        self._tick: dict[int, list] = {}            # pid -> [(start, ticker)] sorted
        self._start: dict[int, object] = {}
        self._end: dict[int, tuple] = {}             # pid -> (date, reason, ret)
        self._issuer: dict[int, object] = {}
        self._by_ticker: dict[str, list] = defaultdict(list)   # ticker -> [(start, end or None, pid)]

    def list(self, pid: int, ticker: str, date, issuer=None) -> None:
        if pid in self._start:
            raise ValueError(f"permanent id {pid} is already used")
        if self.resolve(ticker, date) is not None:
            raise ValueError(f"ticker {ticker} is held on {date!r}")
        self._start[pid], self._tick[pid], self._issuer[pid] = date, [(date, ticker)], issuer
        self._by_ticker[ticker].append([date, None, pid])

    def rename(self, pid: int, ticker: str, date) -> None:
        if self.resolve(ticker, date) is not None:
            raise ValueError(f"ticker {ticker} is held on {date!r}")
        old = self.ticker(pid, date)
        self._close(old, pid, date, exclusive=True)
        self._tick[pid].append((date, ticker))
        self._by_ticker[ticker].append([date, None, pid])

    def delist(self, pid: int, date, reason: str, ret: float | None = None) -> None:
        self._end[pid] = (date, reason, ret)
        self._close(self.ticker(pid, date), pid, date, exclusive=False)

    def _close(self, ticker, pid, date, exclusive: bool) -> None:
        for span in self._by_ticker[ticker]:
            if span[2] == pid and span[1] is None:
                span[1] = (date, "excl") if exclusive else (date, "incl")

    @staticmethod
    def _covers(span, date) -> bool:
        start, end, _ = span
        if date < start:
            return False
        if end is None:
            return True
        d, kind = end
        return date < d if kind == "excl" else date <= d

    def resolve(self, ticker: str, date):
        for span in self._by_ticker.get(ticker, []):
            if self._covers(span, date):
                return span[2]
        return None

    def ticker(self, pid: int, date):
        if pid not in self._start or date < self._start[pid]:
            return None
        if pid in self._end and date > self._end[pid][0]:
            return None
        rows = self._tick[pid]
        i = bisect.bisect_right([d for d, _ in rows], date) - 1
        return rows[i][1]

    def listed(self, date) -> set:
        return {p for p in self._start if self.ticker(p, date) is not None}

    def spans(self, pid: int) -> list:
        out = []
        for ticker, spans in self._by_ticker.items():
            for start, end, p in spans:
                if p == pid:
                    out.append((start, None if end is None else end[0], ticker))
        return sorted(out, key=lambda x: x[0])

    def delisting(self, pid: int):
        return self._end.get(pid)

    def reused(self) -> dict:
        return {t: sorted({s[2] for s in spans}) for t, spans in self._by_ticker.items()
                if len({s[2] for s in spans}) > 1}


def buffered_universe(dates, scores, n: int, exit_rank: int | None = None) -> dict:
    """At each date, rank the names by score (liquidity known at that date, highest first). Members keep
    their place while their rank is at most exit_rank (n by default: no buffer); the free places go to the
    best-ranked non-members, so the universe has n names whenever n are available."""
    exit_rank = exit_rank or n
    out, members = {}, set()
    for d in dates:
        s = scores(d)
        ranked = sorted(s, key=lambda k: (-s[k], k))
        rank = {k: i + 1 for i, k in enumerate(ranked)}
        keep = {k for k in members if k in rank and rank[k] <= exit_rank}
        keep = set(sorted(keep, key=lambda k: rank[k])[:n])
        for k in ranked:
            if len(keep) >= n:
                break
            keep.add(k)
        out[d], members = keep, keep
    return out


def churn(universe: dict) -> float:
    """Average share of the universe replaced at each rebalance after the first."""
    ds = list(universe)
    changes = [len(universe[b] - universe[a]) / max(1, len(universe[b])) for a, b in zip(ds, ds[1:], strict=False)]
    return sum(changes) / len(changes) if changes else 0.0
