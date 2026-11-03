from operator import itemgetter


def by_symbol_then_notional(trades):
    """Symbol ascending, notional descending; equal trades keep their order."""
    out = sorted(trades, key=itemgetter(1), reverse=True)
    out.sort(key=itemgetter(0))
    return out
