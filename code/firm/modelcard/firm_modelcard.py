"""firm.modelcard -- explanations, their stability, and the documents a learned model is validated with (Book 12,
chapter 21).

Global explanations (partial dependence, individual conditional expectation, accumulated local effects, a shallow
global surrogate tree with its fidelity), a local counterfactual search, the stability of feature rankings across
retrains, a model card rendered from a record, and a validation checklist whose numeric checks run through Book 6's
firm.modelval benchmarking harness and binomial outcome test.

API (stable):
    partial_dependence(predict, X, j, grid) -> mean prediction with feature j set to each grid value
    ice(predict, X, j, grid, rows) -> (rows, grid) curves, one per observation
    ale(predict, X, j, bins) -> (edges, centred accumulated local effect at the edges)   Apley and Zhu
    global_surrogate(predict, X, depth, seed) -> (tree, fidelity R^2 on X)
    counterfactual(predict, x, j, target, grid) -> the value of feature j nearest x[j] whose prediction crosses target
    rank_stability(rankings, top) -> (share of rankings whose top set equals the first's, mean Kendall tau of the top
                                      features' ranks)
    ModelCard(fields).render() -> text ; CARD_FIELDS
    validation_checklist(checks) -> list of (item, passed, evidence) ; outcome_check, benchmark_check helpers
"""
from __future__ import annotations

import pathlib
import sys
from dataclasses import dataclass, field

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "modelval"))
import firm_modelval as mv  # noqa: E402


def partial_dependence(predict, X, j, grid):
    out = []
    for v in grid:
        Z = X.copy()
        Z[:, j] = v
        out.append(float(np.mean(predict(Z))))
    return np.array(out)


def ice(predict, X, j, grid, rows):
    out = np.empty((len(rows), len(grid)))
    for k, v in enumerate(grid):
        Z = X[rows].copy()
        Z[:, j] = v
        out[:, k] = predict(Z)
    return out


def ale(predict, X, j, bins=20):
    """First-order accumulated local effect: within each quantile bin of feature j, the mean change in prediction when
    j moves from the bin's lower to its upper edge, the other features kept at their observed values; accumulated
    over bins and centred to mean zero over the data."""
    x = X[:, j]
    edges = np.unique(np.quantile(x, np.linspace(0, 1, bins + 1)))
    idx = np.clip(np.searchsorted(edges, x, side="right") - 1, 0, len(edges) - 2)
    local = np.zeros(len(edges) - 1)
    counts = np.zeros(len(edges) - 1)
    for b in range(len(edges) - 1):
        rows = idx == b
        if not rows.any():
            continue
        lo, hi = X[rows].copy(), X[rows].copy()
        lo[:, j], hi[:, j] = edges[b], edges[b + 1]
        local[b] = float(np.mean(predict(hi) - predict(lo)))
        counts[b] = rows.sum()
    acc = np.r_[0.0, np.cumsum(local)]
    mid = 0.5 * (acc[:-1] + acc[1:])
    return edges, acc - float((mid * counts).sum() / counts.sum())


def global_surrogate(predict, X, depth=3, seed=0):
    from sklearn.tree import DecisionTreeRegressor

    p = predict(X)
    tree = DecisionTreeRegressor(max_depth=depth, random_state=seed).fit(X, p)
    r = p - tree.predict(X)
    return tree, float(1 - r.var() / p.var())


def counterfactual(predict, x, j, target, grid):
    """Among grid values of feature j, the one closest to x[j] that puts the prediction on the other side of target."""
    base = float(predict(x[None])[0])
    side = base >= target
    best = None
    for v in sorted(grid, key=lambda g: abs(g - x[j])):
        z = x.copy()
        z[j] = v
        if (float(predict(z[None])[0]) >= target) != side:
            best = float(v)
            break
    return best


def _kendall(a, b):
    n, c = len(a), 0
    for i in range(n):
        for k in range(i + 1, n):
            c += np.sign(a[i] - a[k]) * np.sign(b[i] - b[k])
    return c / (n * (n - 1) / 2)


def rank_stability(rankings, top=5):
    """rankings: list of feature-index arrays, most important first. The share of retrains whose top-`top` set equals
    the first retrain's, and the mean Kendall tau between the first retrain's top features' ranks and each other's."""
    ref = list(rankings[0][:top])
    same = [set(r[:top]) == set(ref) for r in rankings[1:]]
    taus = []
    for r in rankings[1:]:
        pos = {f: i for i, f in enumerate(r)}
        taus.append(_kendall(list(range(top)), [pos[f] for f in ref]))
    return float(np.mean(same)), float(np.mean(taus))


CARD_FIELDS = ("name", "version", "owner", "purpose", "target", "horizon", "data", "features", "training",
               "validation", "performance", "explanations", "limitations", "monitoring", "approvals")


@dataclass
class ModelCard:
    """A model card (Mitchell and co-authors): one page that says what the model is for, what it was trained and
    tested on, how well it does, how it behaves, where it fails, and who signed it off."""
    fields: dict = field(default_factory=dict)

    def missing(self):
        return [f for f in CARD_FIELDS if not self.fields.get(f)]

    def render(self):
        lines = [f"MODEL CARD: {self.fields.get('name', '?')} (version {self.fields.get('version', '?')})"]
        for f in CARD_FIELDS[2:]:
            v = self.fields.get(f) or "MISSING"
            lines.append(f"{f.upper()}: {v}")
        return "\n".join(lines)


def benchmark_check(candidate, reference, grid, abs_tol, rel_tol):
    """Book 6's harness: the candidate against an independent implementation over a grid."""
    return mv.summary(mv.benchmark(candidate, reference, grid, abs_tol, rel_tol))


def outcome_check(n, exceptions, p, level=0.05):
    """Book 6's binomial outcomes test: passes if the tail probability of at least `exceptions` in n is above level."""
    tail = mv.binomial_tail(n, exceptions, p)
    return tail > level, tail


def validation_checklist(checks):
    """checks: {item: (passed, evidence)}. Returns the list in a fixed order, items not supplied marked as not run."""
    items = ("conceptual soundness", "data and leakage", "out-of-sample performance", "challenger comparison",
             "stability across retrains", "explanations sane", "implementation parity", "outcomes analysis",
             "monitoring in place")
    return [(k, bool(checks.get(k, (False,))[0]), checks.get(k, (False, "not run"))[1]) for k in items]
