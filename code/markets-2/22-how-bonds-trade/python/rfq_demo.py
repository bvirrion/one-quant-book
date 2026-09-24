"""Chapter 22 of Book 2: how bonds trade. The client's expected cost of an RFQ by the number of
dealers asked, with and without information leakage, simulated winning bids, and a composite price.
All parameters are illustrative (basis points of price)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/rfq"))
from firm_rfq import best_n, composite, expected_cost, expected_max_normal, simulate_rfq

MARKUP, SIGMA = 10.0, 5.0            # dealers' average markup and the spread of their private terms, bp
LEAKS = (0.5, 1.0, 1.5)             # cost per losing dealer, bp
NOTIONAL = 25e6


def cost_table(n_max: int = 8) -> list[tuple[int, float, float, float, float]]:
    return [(n, expected_max_normal(n), *(expected_cost(n, MARKUP, SIGMA, lk) for lk in LEAKS))
            for n in range(1, n_max + 1)]


def histograms(ns: tuple[int, ...] = (1, 3, 6), lo: float = -10.0, hi: float = 26.0, bins: int = 36):
    width = (hi - lo) / bins
    out = []
    for n in ns:
        sims = simulate_rfq(n, MARKUP, SIGMA, trials=40_000, seed=n)
        counts = [0] * bins
        for x in sims:
            k = int((x - lo) // width)
            if 0 <= k < bins:
                counts[k] += 1
        out.append((n, [(lo + (k + 0.5) * width, c / len(sims) / width) for k, c in enumerate(counts)]))
    return out


def problem() -> dict[str, float]:
    n_star = best_n(MARKUP, SIGMA, 1.0)
    c = {n: expected_cost(n, MARKUP, SIGMA, 1.0) for n in (1, 2, 3, 4, 6)}
    return {"n_star": n_star, "cost_star": c[n_star], "cost_1": c[1], "cost_6": c[6], "cost_2": c[2], "cost_4": c[4],
            "usd_star": c[n_star] * 1e-4 * NOTIONAL, "usd_1": c[1] * 1e-4 * NOTIONAL,
            "n_star_low": best_n(MARKUP, SIGMA, 0.5), "n_star_high": best_n(MARKUP, SIGMA, 1.5),
            "saving_vs_6": (c[6] - c[n_star]) * 1e-4 * NOTIONAL}


def composite_example() -> float:
    return composite([(99.42, 10), (99.45, 40), (99.40, 90), (99.47, 5), (98.20, 20)])
