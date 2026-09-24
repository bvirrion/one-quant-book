"""Margin through a volatility shock: scenario and value-at-risk methods (Chapter 20). Illustrative."""
import numpy as np


def simulate_returns(n: int, calm_vol: float, stress_vol: float, start: int, length: int, seed: int) -> np.ndarray:
    """Daily returns with a block of stressed volatility that decays back to calm."""
    rng = np.random.default_rng(seed)
    vol = np.full(n, calm_vol)
    vol[start:start + length] = stress_vol
    tail = np.arange(n - start - length)
    vol[start + length:] = calm_vol + (stress_vol - calm_vol) * np.exp(-tail / 25.0)
    return rng.standard_normal(n) * vol


def hs_var(returns: np.ndarray, t: int, lookback: int, q: float, horizon: int) -> float:
    """Plain historical simulation: the q-quantile loss of the last `lookback` days, scaled by sqrt(horizon)."""
    window = returns[t - lookback:t]
    return float(-np.quantile(window, 1.0 - q)) * np.sqrt(horizon)


def ewma_vol(returns: np.ndarray, lam: float = 0.97) -> np.ndarray:
    """Volatility known at the START of each day (uses returns up to the day before)."""
    var = np.empty(len(returns))
    var[0] = returns[:60].var()
    for i in range(1, len(returns)):
        var[i] = lam * var[i - 1] + (1.0 - lam) * returns[i - 1] ** 2
    return np.sqrt(var)


def fhs_var(returns: np.ndarray, vol: np.ndarray, t: int, lookback: int, q: float, horizon: int) -> float:
    """Filtered historical simulation: past returns rescaled to today's volatility."""
    window = returns[t - lookback:t] / vol[t - lookback:t] * vol[t]
    return float(-np.quantile(window, 1.0 - q)) * np.sqrt(horizon)


def with_floor(margin: np.ndarray, stressed: float, weight: float) -> np.ndarray:
    """An anti-procyclicality tool: a weight on a fixed stressed-period margin."""
    return (1.0 - weight) * margin + weight * stressed


def peak_to_trough(margin: np.ndarray, window: int) -> float:
    """Largest increase of the margin over any `window` days, as a fraction of its starting level."""
    ratio = margin[window:] / margin[:-window]
    return float(ratio.max() - 1.0)
