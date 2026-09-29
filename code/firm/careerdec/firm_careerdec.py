"""firm.careerdec -- choosing among offers with several attributes (build of One Quant Book 17, chapter 30).

Each offer is scored on attributes that the earlier chapters' tools measure (the pay's expected value and spread with
firm.payoffer, what tax and housing take with firm.locations, on-call load with firm.workload, a career's value with
firm.careerpath) and on judgements the chooser states. Scores are scaled from the worst to the best offer on each
attribute (0 to 1), weighted by swing weights, and added: the multi-attribute value model of Keeney and Raiffa. A
dominated offer is dropped first. Because weights are uncertain, rank acceptability (Lahdelma, Hokkanen and Salminen's
SMAA) samples weights uniformly on the simplex and reports how often each offer takes each rank; and the smallest shift
of one attribute's weight that changes the best offer says how robust the choice is.

API (stable):
    scale(matrix, higher_better) -> (n_offers, n_attrs) in [0, 1]
    swing_weights(points) -> weights summing to one
    value(scaled, weights) -> (n_offers,)
    dominated(matrix, higher_better) -> indices of dominated offers
    rank_acceptability(scaled, n, rng) -> (n_offers, n_offers): share of weight draws giving each offer each rank
    flip_shift(scaled, weights, attr, step) -> smallest change of weight[attr] (others rescaled) that changes the best
"""
import numpy as np


def scale(matrix, higher_better):
    m = np.asarray(matrix, float)
    lo, hi = m.min(axis=0), m.max(axis=0)
    span = np.where(hi > lo, hi - lo, 1.0)
    s = (m - lo) / span
    hb = np.asarray(higher_better, bool)
    return np.where(hb, s, 1.0 - s)


def swing_weights(points):
    p = np.asarray(points, float)
    return p / p.sum()


def value(scaled, weights):
    return np.asarray(scaled, float) @ np.asarray(weights, float)


def dominated(matrix, higher_better):
    m = np.asarray(matrix, float) * np.where(np.asarray(higher_better, bool), 1.0, -1.0)
    out = []
    for i in range(len(m)):
        if any(np.all(m[j] >= m[i]) and np.any(m[j] > m[i]) for j in range(len(m)) if j != i):
            out.append(i)
    return out


def rank_acceptability(scaled, n, rng):
    s = np.asarray(scaled, float)
    w = rng.dirichlet(np.ones(s.shape[1]), n)
    v = w @ s.T                                   # (n, offers)
    ranks = (-v).argsort(axis=1).argsort(axis=1)  # 0 = best
    k = s.shape[0]
    return np.stack([(ranks == r).mean(axis=0) for r in range(k)], axis=1)


def _shifted(weights, attr, new):
    w = np.asarray(weights, float).copy()
    rest = 1.0 - w[attr]
    w = w * ((1.0 - new) / rest) if rest > 0 else w
    w[attr] = new
    return w


def flip_shift(scaled, weights, attr, step=0.001):
    """Smallest |change| of weights[attr] (the others rescaled in proportion) that changes the best offer; returns
    (signed change, new best index) or None if no change in [0, 1] does."""
    best = int(np.argmax(value(scaled, weights)))
    w0 = float(np.asarray(weights)[attr])
    for k in range(1, int(1.0 / step) + 1):
        for sign in (1, -1):
            new = w0 + sign * k * step
            if 0.0 <= new <= 1.0:
                b = int(np.argmax(value(scaled, _shifted(weights, attr, new))))
                if b != best:
                    return sign * k * step, b
    return None
