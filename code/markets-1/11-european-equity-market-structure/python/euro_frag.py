"""Fragmentation, the European best bid and offer, and the volume cap (Chapter 11)."""
import numpy as np

# Cboe, European equities briefing for July 2026 (published 17 Aug 2026); ledger row F4.
ON_EXCHANGE_JULY_2026 = {"Central limit order books": 52.8, "Closing auctions": 24.3,
                         "Periodic auctions": 10.4, "Non-displayed order books": 10.9}
ON_EXCHANGE_ADVT_BN, ADDRESSABLE_ADVT_BN, SI_ADVT_BN = 57.5, 80.0, 14.3
VOLUME_CAP = 0.07


def herfindahl(shares) -> float:
    s = np.asarray(list(shares), dtype=float)
    s = s / s.sum()
    return float((s * s).sum())


def effective_venues(shares) -> float:
    """1 / HHI: the number of equal-sized venues that would give the same concentration."""
    return 1.0 / herfindahl(shares)


def ebbo(quotes: dict[str, tuple[float, float]]) -> tuple[float, float, list[str], list[str]]:
    """European best bid and offer from {venue: (bid, ask)}; no protection rule, no size filter."""
    bid = max(b for b, _ in quotes.values())
    ask = min(a for _, a in quotes.values())
    return (bid, ask, sorted(v for v, (b, _) in quotes.items() if b == bid),
            sorted(v for v, (_, a) in quotes.items() if a == ask))


def cap_usage(waiver_volume: np.ndarray, total_volume: np.ndarray, window: int = 12) -> np.ndarray:
    """Rolling share of volume traded under the reference price waiver over `window` months."""
    w = np.convolve(waiver_volume, np.ones(window), mode="valid")
    t = np.convolve(total_volume, np.ones(window), mode="valid")
    return w / t


def simulate_cap(months: int = 36, seed: int = 11, suspension: int = 3):
    """A stock whose dark share drifts up until the 7 % cap suspends the waiver for three months.

    While suspended, dark volume is zero and is redistributed: 50 % periodic auctions,
    30 % lit books, 20 % systematic internalisers."""
    rng = np.random.default_rng(seed)
    total = 100.0 + rng.normal(0, 4, months)
    wish = np.clip(0.045 + 0.0012 * np.arange(months) + rng.normal(0, 0.003, months), 0, 1)
    dark = np.zeros(months)
    periodic, lit, si = 0.08 * total, np.zeros(months), 0.15 * total
    usage = np.full(months, np.nan)
    suspended_until = -1
    for m in range(months):
        if m <= suspended_until:
            moved = wish[m] * total[m]
            periodic[m] += 0.5 * moved
            si[m] += 0.2 * moved          # the remaining 30 % returns to the lit books
        else:
            dark[m] = wish[m] * total[m]
        lit[m] = total[m] - dark[m] - periodic[m] - si[m]
        if m >= 11:
            usage[m] = dark[m - 11:m + 1].sum() / total[m - 11:m + 1].sum()
            if usage[m] > VOLUME_CAP and m > suspended_until:
                suspended_until = m + suspension
    return {"total": total, "dark": dark, "periodic": periodic, "lit": lit, "si": si, "usage": usage}
