"""FX settlement exposure over the settlement day (build of Book 2, Chapter 20).

Each currency has two times, in hours of the settlement day in GMT: the unilateral cancellation
deadline after which a payment in it can no longer be recalled, and the time at which a payment
received in it is final and confirmed. A trade that sells currency A and buys B exposes its seller
to the full value of B from A's deadline until B's confirmation. Values are in US dollars.
"""
from collections import defaultdict
from dataclasses import dataclass


@dataclass(frozen=True)
class Trade:
    counterparty: str
    sell: str
    buy: str
    value_usd: float          # value of each leg at the trade's rate


def window(trade: Trade, times: dict[str, tuple[float, float]]) -> tuple[float, float]:
    """(start, end) of the exposure: the sold currency's cancellation deadline to the bought
    currency's confirmation; empty if the latter comes first."""
    start, end = times[trade.sell][0], times[trade.buy][1]
    return (start, end) if end > start else (start, start)


def exposure_at(t: float, trades: list[Trade], times: dict[str, tuple[float, float]]) -> float:
    return sum(tr.value_usd for tr in trades if window(tr, times)[0] <= t < window(tr, times)[1])


def net_by_counterparty(trades: list[Trade]) -> list[Trade]:
    """Payment netting: per counterparty and currency, pay only the net amount. Net flows are
    re-paired, largest first, into trades that sell a net-paid currency and buy a net-received one."""
    out = []
    by_cp: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for tr in trades:
        by_cp[tr.counterparty][tr.sell] -= tr.value_usd
        by_cp[tr.counterparty][tr.buy] += tr.value_usd
    for cp, flows in by_cp.items():
        pays = sorted(((c, -v) for c, v in flows.items() if v < -1e-9), key=lambda x: -x[1])
        gets = sorted(((c, v) for c, v in flows.items() if v > 1e-9), key=lambda x: -x[1])
        i = j = 0
        while i < len(pays) and j < len(gets):
            amt = min(pays[i][1], gets[j][1])
            out.append(Trade(cp, pays[i][0], gets[j][0], amt))
            pays[i], gets[j] = (pays[i][0], pays[i][1] - amt), (gets[j][0], gets[j][1] - amt)
            i += pays[i][1] <= 1e-9
            j += gets[j][1] <= 1e-9
    return out


def profile(trades: list[Trade], times: dict[str, tuple[float, float]], pvp: set[str] = frozenset(),
            step: float = 0.25, start: float = -12.0, end: float = 24.0) -> list[tuple[float, float]]:
    """Exposure through the day; trades whose two currencies are both in `pvp` carry none."""
    live = [tr for tr in trades if not (tr.sell in pvp and tr.buy in pvp)]
    n = int(round((end - start) / step))
    return [(start + k * step, exposure_at(start + k * step, live, times)) for k in range(n + 1)]


def peak(prof: list[tuple[float, float]]) -> float:
    return max(v for _, v in prof)
