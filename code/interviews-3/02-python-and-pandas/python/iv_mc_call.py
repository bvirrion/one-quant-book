import numpy as np


def mc_call(spot, strike, rate, vol, t, pairs, rng, chunk=500_000):
    """Antithetic estimate of a European call: returns (price, standard error)."""
    drift = (rate - 0.5 * vol * vol) * t
    root = vol * np.sqrt(t)
    n, total, squares = 0, 0.0, 0.0
    while n < pairs:                               # memory is bounded by chunk
        m = min(chunk, pairs - n)
        z = rng.standard_normal(m)
        up = np.maximum(spot * np.exp(drift + root * z) - strike, 0.0)
        down = np.maximum(spot * np.exp(drift - root * z) - strike, 0.0)
        one = 0.5 * (up + down)                    # one sample per pair
        total += one.sum()
        squares += (one * one).sum()
        n += m
    mean = total / pairs
    var = max(squares / pairs - mean * mean, 0.0)
    disc = np.exp(-rate * t)
    return disc * mean, disc * np.sqrt(var / pairs)
