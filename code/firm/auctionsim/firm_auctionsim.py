"""firm.auctionsim -- auction phases on the exchange simulator (build of One Quant Book 10, chapter 10).

firm.exchsim's engine runs the calls (orders accepted without matching, indicative publication, the at-close cut-off,
the uncross through Book 1's firm_auction) and frequent batch auctions; this module states an auction design as a
policy, turns it into the simulator's configuration, and reads the results.

API (stable):
    ClosingAuction(call_s=300, indicative_s=1, cutoff_s=None, collar=0.0, random_end_s=0)
        .phases(open_ns, close_ns, end_ns) -> Phases    a closing call starting call_s before the close, indicatives
                                                        every indicative_s, at-close entry frozen cutoff_s before the
                                                        close, the uncross at a uniform random time in
                                                        [close, close + random_end_s)
        .controls(venue, close_ns, ref_price) -> [(t_ns, venue, Ctl)]   the collar: a price band of +-collar around
                                                        ref_price from the start of the call (orders outside it
                                                        are rejected, so the uncross stays inside)
    batch_venue(interval_ms, **kw) -> ExchangeConfig    frequent batch auctions every interval_ms
    indicatives(res, venue, locate) -> array            (t_ns, paired, imbalance signed + buy, price) of every I
    final_cross(res, venue, locate) -> (t_ns, price, volume)   the closing cross (Q with cross type C)
    gap_path(ind, final, grid_s) -> array               |indicative - final| (ticks of `tick`) against seconds to the
                                                        uncross, last indicative before each grid point
"""
from __future__ import annotations

import pathlib
import sys
from dataclasses import dataclass, replace

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "exchsim"))
from firm_exchsim import SEC, ExchangeConfig, Phases  # noqa: E402
from firm_exchsim_codec import NT  # noqa: E402

CTL = NT["ctl"]


@dataclass(frozen=True)
class ClosingAuction:
    call_s: float = 300.0
    indicative_s: float = 1.0
    cutoff_s: float | None = None
    collar: float = 0.0
    random_end_s: float = 0.0

    def phases(self, open_ns: int, close_ns: int, end_ns: int) -> Phases:
        cutoff = None if self.cutoff_s is None else close_ns - int(self.cutoff_s * SEC)
        return Phases(start_ns=open_ns - SEC, open_ns=open_ns, close_ns=close_ns, end_ns=end_ns,
                      close_auction=True, close_call_ns=close_ns - int(self.call_s * SEC),
                      indicative_every_ns=int(self.indicative_s * SEC), moc_cutoff_ns=cutoff,
                      random_end_ns=int(self.random_end_s * SEC))

    def controls(self, venue: str, close_ns: int, ref_price: int, tick: int = 100) -> list:
        if not self.collar:
            return []
        lo = int(ref_price * (1 - self.collar)) // tick * tick
        hi = -(-int(ref_price * (1 + self.collar)) // tick) * tick
        return [(close_ns - int(self.call_s * SEC), venue, CTL["R"](1, ref_price, lo, hi))]


def batch_venue(interval_ms: float, **kw) -> ExchangeConfig:
    return replace(ExchangeConfig(venue="SIMP", batch_interval_ns=int(interval_ms * 1_000_000)), **kw)


def indicatives(res, venue: str = "", locate: int = 1) -> np.ndarray:
    rows = [(ts, m.paired, m.imbalance * (1 if m.direction == "B" else -1 if m.direction == "S" else 0), m.near)
            for ts, _, m in res.feed_messages(venue)
            if type(m).__name__ == "Feed_I" and m.locate == locate and m.direction != "O"]
    return np.array(rows, dtype=[("t", "i8"), ("paired", "i8"), ("imbalance", "i8"), ("price", "i8")])


def final_cross(res, venue: str = "", locate: int = 1):
    for ts, _, m in res.feed_messages(venue):
        if type(m).__name__ == "Feed_Q" and m.locate == locate and m.cross_type == "C":
            return ts, m.price, m.shares
    return None


def gap_path(ind: np.ndarray, final: tuple, grid_s, tick: int = 100) -> np.ndarray:
    t_end, p_end = final[0], final[1]
    out = []
    for g in grid_s:
        i = np.searchsorted(ind["t"], t_end - int(g * SEC), side="right") - 1
        out.append(abs(int(ind["price"][i]) - p_end) / tick if i >= 0 else np.nan)
    return np.array(out)
