"""firm.fragmentation -- where volume trades, and the volume cap (build of Chapter 11)."""
from collections import defaultdict
from dataclasses import dataclass

MECHANISMS = ("lit", "dark_rpw", "dark_lis", "periodic", "auction", "si")
CAP = 0.07
WINDOW = 12


@dataclass(frozen=True)
class VenueTrade:
    instrument: str
    venue: str
    mechanism: str
    value: int          # ledger units
    month: int          # consecutive month index


class Monitor:
    def __init__(self) -> None:
        self._by = {"venue": defaultdict(lambda: defaultdict(int)),
                    "mechanism": defaultdict(lambda: defaultdict(int))}
        self._total = defaultdict(lambda: defaultdict(int))     # instrument -> month -> value
        self._rpw = defaultdict(lambda: defaultdict(int))

    def add(self, t: VenueTrade) -> None:
        if t.mechanism not in MECHANISMS:
            raise ValueError(f"unknown mechanism {t.mechanism!r}")
        if t.value <= 0:
            raise ValueError("value must be positive")
        self._by["venue"][t.instrument][t.venue] += t.value
        self._by["mechanism"][t.instrument][t.mechanism] += t.value
        self._total[t.instrument][t.month] += t.value
        if t.mechanism == "dark_rpw":
            self._rpw[t.instrument][t.month] += t.value

    def shares(self, instrument: str, by: str) -> dict[str, float]:
        d = self._by[by][instrument]
        tot = sum(d.values())
        return {k: v / tot for k, v in d.items()}

    def effective_venues(self, instrument: str) -> float:
        return 1.0 / sum(s * s for s in self.shares(instrument, "venue").values())

    def _window(self, instrument: str, month: int, length: int):
        months = range(month - length + 1, month + 1)
        if any(m not in self._total[instrument] for m in months):
            return None
        return (sum(self._rpw[instrument][m] for m in months), sum(self._total[instrument][m] for m in months))

    def cap_usage(self, instrument: str, month: int):
        w = self._window(instrument, month, WINDOW)
        return None if w is None else w[0] / w[1]

    def headroom(self, instrument: str, month: int, next_total: int):
        """Waiver value next month that brings usage over the window ending next month exactly to the cap."""
        w = self._window(instrument, month, WINDOW - 1)
        return None if w is None else CAP * (w[1] + next_total) - w[0]
