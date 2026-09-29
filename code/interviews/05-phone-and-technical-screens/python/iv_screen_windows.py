"""Book 18, chapter 5: a screen question with a planted off-by-one, and its fix."""


def moving_averages_buggy(prices, k):
    """Average of each window of k consecutive prices (as submitted in the screen)."""
    out = []
    for i in range(len(prices) - k):
        out.append(sum(prices[i : i + k]) / k)
    return out


def moving_averages(prices, k):
    """The fix: there are len(prices) - k + 1 windows; running sum, O(n)."""
    if k <= 0 or k > len(prices):
        return []
    s = sum(prices[:k])
    out = [s / k]
    for i in range(k, len(prices)):
        s += prices[i] - prices[i - k]
        out.append(s / k)
    return out
