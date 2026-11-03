"""Paying from coins: inputs are used up whole, and change is a new coin."""


def spend(coins, pay, fee):
    """Largest coins first. Returns (inputs used, change, coins left), or ValueError."""
    used, total = [], 0
    for coin in sorted(coins, reverse=True):
        if total >= pay + fee:
            break
        used.append(coin)
        total += coin
    if total < pay + fee:
        raise ValueError("not enough")
    left = sorted(coins)
    for coin in used:
        left.remove(coin)
    return used, total - pay - fee, left
