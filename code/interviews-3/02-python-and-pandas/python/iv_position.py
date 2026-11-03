import numpy as np


def capped_position(trades, limit):
    """Each order is cut to fit; the next one starts from the cut position."""
    pos, out = 0, []
    for q in trades:
        pos = max(-limit, min(limit, pos + q))
        out.append(pos)
    return out


def wrong_clip(trades, limit):
    return np.clip(np.cumsum(trades), -limit, limit).tolist()


def capped_above(trades, limit):
    """A cap on one side only has a closed form."""
    c = np.cumsum(trades)
    return (c - np.maximum(np.maximum.accumulate(c) - limit, 0)).tolist()
