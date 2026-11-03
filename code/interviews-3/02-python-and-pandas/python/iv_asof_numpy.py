import numpy as np


def asof(trade_sym, trade_t, quote_sym, quote_t):
    """Row of the latest quote at or before each trade, same symbol; -1 if none."""
    if len(quote_t) == 0:
        return np.full(len(trade_t), -1)
    times, ranks = np.unique(np.concatenate([trade_t, quote_t]), return_inverse=True)
    span = len(times)                      # int64 codes: sym * span cannot overflow
    trade_key = np.asarray(trade_sym, dtype=np.int64) * span + ranks[: len(trade_t)]
    quote_key = np.asarray(quote_sym, dtype=np.int64) * span + ranks[len(trade_t) :]
    order = np.argsort(quote_key, kind="stable")     # equal keys keep arrival order
    i = np.searchsorted(quote_key[order], trade_key, side="right") - 1
    found = order[np.maximum(i, 0)]
    return np.where((i >= 0) & (quote_sym[found] == trade_sym), found, -1)
