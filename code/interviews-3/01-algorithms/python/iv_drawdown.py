def max_drawdown(prices):
    peak = None
    worst = 0
    for p in prices:
        if peak is None or p > peak:
            peak = p
        worst = max(worst, peak - p)
    return worst


def max_relative_drawdown(prices):
    """The same scan, as a fraction of the peak. Prices must be positive."""
    peak, worst = None, 0
    for p in prices:
        if peak is None or p > peak:
            peak = p
        worst = max(worst, (peak - p) / peak)
    return worst


def best_trade(prices):
    """Largest profit from one buy and one later sell: the mirror image, with a running low."""
    low, best = None, 0
    for p in prices:
        if low is None or p < low:
            low = p
        best = max(best, p - low)
    return best
