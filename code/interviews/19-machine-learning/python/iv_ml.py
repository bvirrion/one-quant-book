"""Book 18, chapter 19: machine-learning interview demonstrations on generated data (scikit-learn).

Every series here is pure noise or a stated planted relation; the demonstrations show what validation and
regularisation do, not a trading result.
"""
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Lasso, Ridge
from sklearn.model_selection import KFold
from sklearn.neighbors import KNeighborsRegressor


def r2(y, p):
    return 1 - np.sum((y - p) ** 2) / np.sum((y - y.mean()) ** 2)


def noise_panel(seed: int, n: int = 2000, horizon: int = 20):
    """Random-walk prices with no predictability; features are trailing 20-, 60- and 120-day returns and the
    label is the next `horizon`-day return (overlapping labels)."""
    rng = np.random.default_rng(seed)
    c = np.cumsum(rng.standard_normal(n + horizon + 120) * 0.01)
    idx = np.arange(120, n + 120)
    x = np.column_stack([c[idx] - c[idx - 20], c[idx] - c[idx - 60], c[idx] - c[idx - 120]])
    y = c[idx + horizon] - c[idx]
    return x, y


def cv_shuffled(x, y, seed: int, k: int = 5) -> float:
    pred = np.empty_like(y)
    for tr, te in KFold(k, shuffle=True, random_state=seed).split(x):
        pred[te] = KNeighborsRegressor(5).fit(x[tr], y[tr]).predict(x[te])
    return r2(y, pred)


def walk_forward(x, y, horizon: int = 20, folds: int = 5) -> float:
    """Expanding-window evaluation; training data end `horizon` days before each test block (purging)."""
    n = len(y)
    size = n // (folds + 1)
    ys, ps = [], []
    for k in range(1, folds + 1):
        te = np.arange(k * size, (k + 1) * size)
        tr = np.arange(0, k * size - horizon)
        ps.append(KNeighborsRegressor(5).fit(x[tr], y[tr]).predict(x[te]))
        ys.append(y[te])
    return r2(np.concatenate(ys), np.concatenate(ps))


def leak_study(seeds, n: int = 2000):
    out = []
    for s in seeds:
        x, y = noise_panel(s, n)
        out.append((cv_shuffled(x, y, s), walk_forward(x, y)))
    return np.array(out)


def lasso_instability(seeds, n: int = 100, rho: float = 0.99, alpha: float = 0.5):
    """Two features with correlation rho, y = x1 + x2 + noise. Share of samples in which the lasso zeroes one of
    the two coefficients, and the average ridge coefficients."""
    zeroed, ridge_coefs = 0, []
    for s in seeds:
        rng = np.random.default_rng(s)
        z = rng.standard_normal((n, 2))
        x1 = z[:, 0]
        x2 = rho * x1 + np.sqrt(1 - rho * rho) * z[:, 1]
        x = np.column_stack([x1, x2])
        y = x1 + x2 + 2.0 * rng.standard_normal(n)
        coef = Lasso(alpha=alpha).fit(x, y).coef_
        zeroed += int(np.any(np.abs(coef) < 1e-10))
        ridge_coefs.append(Ridge(alpha=10.0).fit(x, y).coef_)
    return zeroed / len(seeds), np.mean(ridge_coefs, axis=0)


def boosting_on_noise(seed: int, n: int = 1000, trees: int = 300):
    rng = np.random.default_rng(seed)
    x = rng.standard_normal((2 * n, 5))
    y = rng.standard_normal(2 * n)
    m = GradientBoostingRegressor(n_estimators=trees, max_depth=3, learning_rate=0.1, random_state=seed)
    m.fit(x[:n], y[:n])
    return r2(y[:n], m.predict(x[:n])), r2(y[n:], m.predict(x[n:]))


def trade_threshold(gain: float, loss: float) -> float:
    """Trade when the probability of being right exceeds loss / (gain + loss)."""
    return loss / (gain + loss)
