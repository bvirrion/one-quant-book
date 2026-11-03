import numpy as np
import pandas as pd


def sharpes(n=25_200, seed=23):
    rng = np.random.default_rng(seed)
    ret = pd.Series(rng.normal(0, 0.01, n))     # pure noise: nothing to find
    signal = np.sign(ret)
    def annual(pnl):
        return pnl.mean() / pnl.std() * np.sqrt(252)
    return annual(signal * ret), annual(signal.shift(1) * ret)
