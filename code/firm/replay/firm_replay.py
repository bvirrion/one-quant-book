"""Incident replay harness (build of Book 1, Chapter 31).

Replays a tape of trades and quotes through the monitors a post-mortem needs: the price bands of
a limit-up-limit-down mechanism, its limit states and pauses, and depth near the mid. The band
rules follow the published description of the US plan: reference price = mean of the trades of
the last five minutes, updated only when it moves 1% or more and at most every 30 seconds; bands
at a percentage either side, doubled near the open and close; a limit state when the best OFFER
reaches the lower band or the best BID reaches the upper band; a pause of five minutes if the
limit state lasts 15 seconds.
"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Tick:
    t: float                         # seconds since the open
    bid: float
    ask: float
    trade: float | None = None       # trade price, if this tick carries one


@dataclass
class Luld:
    band_pct: float                  # 0.05 for 5%
    open_close_double: bool = True
    session: float = 23_400.0        # 6.5 hours
    window: float = 300.0
    min_hold: float = 30.0
    min_move: float = 0.01
    limit_seconds: float = 15.0
    pause_seconds: float = 300.0
    reference: float | None = None
    _ref_time: float = -1e9
    _trades: list[tuple[float, float]] = field(default_factory=list)
    _limit_since: float | None = None
    paused_until: float = -1.0
    events: list[tuple[float, str]] = field(default_factory=list)

    def pct(self, t: float) -> float:
        doubled = self.open_close_double and (t < 900.0 or t >= self.session - 1_500.0)
        return self.band_pct * (2.0 if doubled else 1.0)

    def bands(self, t: float) -> tuple[float, float]:
        p = self.pct(t)
        return self.reference * (1.0 - p), self.reference * (1.0 + p)

    def on_tick(self, k: Tick) -> str:
        """Returns the state after this tick: 'paused', 'limit' or 'normal'."""
        if k.t < self.paused_until:
            return "paused"
        if k.trade is not None:
            self._trades.append((k.t, k.trade))
        self._trades = [(t, p) for t, p in self._trades if t > k.t - self.window]
        if self._trades:
            mean = sum(p for _, p in self._trades) / len(self._trades)
            if self.reference is None:
                self.reference, self._ref_time = mean, k.t
            elif k.t - self._ref_time >= self.min_hold and abs(mean / self.reference - 1.0) >= self.min_move:
                self.reference, self._ref_time = mean, k.t
        if self.reference is None:
            return "normal"
        lo, hi = self.bands(k.t)
        in_limit = k.ask <= lo or k.bid >= hi
        if not in_limit:
            self._limit_since = None
            return "normal"
        if self._limit_since is None:
            self._limit_since = k.t
            self.events.append((k.t, "limit state"))
        if k.t - self._limit_since >= self.limit_seconds:
            self.paused_until = k.t + self.pause_seconds
            self._limit_since = None
            self._trades.clear()
            self.reference = None                  # reopening sets a new reference
            self.events.append((k.t, "pause"))
            return "paused"
        return "limit"


def replay(ticks: list[Tick], luld: Luld) -> list[tuple[float, str, float | None, float | None]]:
    """(time, state, lower band, upper band) for each tick."""
    out = []
    for k in ticks:
        state = luld.on_tick(k)
        lo, hi = luld.bands(k.t) if luld.reference is not None else (None, None)
        out.append((k.t, state, lo, hi))
    return out


def depth_within(levels: list[tuple[float, int]], mid: float, bp: float) -> int:
    """Shares or contracts resting within `bp` basis points of the mid, from (price, size) levels."""
    return sum(q for p, q in levels if abs(p / mid - 1.0) * 1e4 <= bp + 1e-9)
