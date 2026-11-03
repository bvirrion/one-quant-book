import heapq
from collections import Counter


def top_k(trades, k):
    """trades: (symbol, price, qty). The k largest notionals, ties broken by symbol name."""
    notional = Counter()
    for symbol, price, qty in trades:
        notional[symbol] += price * qty
    return heapq.nsmallest(k, notional.items(), key=lambda item: (-item[1], item[0]))
