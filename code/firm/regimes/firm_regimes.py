"""firm.regimes -- clustering, regime models and anomaly scores (Book 12, chapter 20).

Correlation clustering of assets (k-means on standardised return histories and hierarchical clustering on the
correlation distance, with a stability score across sub-samples); a Gaussian hidden Markov model fitted by
expectation-maximisation, with forward filtering (what is known at each date), forward-backward smoothing (what is known
with hindsight) and Viterbi decoding; regime statistics computed from filtered probabilities only; and unsupervised
anomaly scores (isolation forest, autoencoder reconstruction error) evaluated like Book 9's surveillance detectors, by
their true-positive rate at a fixed false-positive rate. NumPy and scikit-learn (one thread).

API (stable):
    market_residuals(R) -> returns minus their beta times the equal-weighted average
    corr_distance(R) -> sqrt(2 (1 - corr)) between the columns of a return matrix
    kmeans_clusters(R, k, seed), hier_clusters(R, k) -> labels ; ari(a, b) adjusted Rand index
    stability(R, k, method) -> ARI between the clusterings of the two halves of the sample
    regime_series(n, means, sds, P, seed) -> (returns, states)            a planted Markov-switching series
    GaussianHMM(k).fit(x, iters, seed) ; .filter(x) -> P(s_t | x_1..t) ; .smooth(x) -> P(s_t | x_1..T) ; .viterbi(x)
    iforest_scores(X, seed), autoencoder_scores(X, seed) -> anomaly scores (higher = more anomalous)
"""
from __future__ import annotations

import numpy as np


def market_residuals(R):
    """Each column minus its beta times the equal-weighted average column: the common factor would otherwise dominate
    every correlation."""
    m = R.mean(1, keepdims=True)
    return R - m * ((R * m).sum(0) / (m * m).sum())


def corr_distance(R):
    C = np.corrcoef(np.asarray(R).T)
    return np.sqrt(np.maximum(2 * (1 - C), 0.0))


def kmeans_clusters(R, k, seed=0):
    from sklearn.cluster import KMeans

    Z = (R - R.mean(0)) / R.std(0)
    return KMeans(k, n_init=10, random_state=seed).fit_predict(Z.T)


def hier_clusters(R, k):
    """Average-linkage hierarchical clustering on the correlation distance (Mantegna's metric)."""
    from scipy.cluster.hierarchy import fcluster, linkage
    from scipy.spatial.distance import squareform

    D = corr_distance(R)
    np.fill_diagonal(D, 0.0)
    return fcluster(linkage(squareform(D, checks=False), "average"), k, "maxclust") - 1


def ari(a, b):
    from sklearn.metrics import adjusted_rand_score

    return float(adjusted_rand_score(a, b))


def stability(R, k, method="hier", seed=0):
    h = len(R) // 2
    f = (lambda X: hier_clusters(X, k)) if method == "hier" else (lambda X: kmeans_clusters(X, k, seed))
    return ari(f(R[:h]), f(R[h:]))


# ---------------------------------------------------------------------------------------------------- regimes
def regime_series(n, means, sds, P, seed=0):
    rng = np.random.default_rng(seed)
    P = np.asarray(P)
    s = np.zeros(n, dtype=int)
    for t in range(1, n):
        s[t] = rng.choice(len(means), p=P[s[t - 1]])
    return np.asarray(means)[s] + np.asarray(sds)[s] * rng.standard_normal(n), s


class GaussianHMM:
    """k hidden states, Gaussian emissions; EM (Baum-Welch) with scaled forward-backward recursions."""

    def __init__(self, k=2):
        self.k = k

    def _dens(self, x):
        return np.exp(-0.5 * ((x[:, None] - self.mu) / self.sd) ** 2) / (self.sd * np.sqrt(2 * np.pi))

    def _forward(self, x):
        B = self._dens(x)
        a = np.zeros((len(x), self.k))
        c = np.zeros(len(x))
        a[0] = self.pi * B[0]
        c[0] = a[0].sum()
        a[0] /= c[0]
        for t in range(1, len(x)):
            a[t] = (a[t - 1] @ self.P) * B[t]
            c[t] = a[t].sum()
            a[t] /= c[t]
        return a, c, B

    def filter(self, x):
        """P(s_t | x_1, ..., x_t): the regime as known at date t."""
        return self._forward(np.asarray(x, float))[0]

    def smooth(self, x):
        """P(s_t | x_1, ..., x_T): the regime as known at the end of the sample."""
        x = np.asarray(x, float)
        a, c, B = self._forward(x)
        b = np.ones((len(x), self.k))
        for t in range(len(x) - 2, -1, -1):
            b[t] = (self.P @ (B[t + 1] * b[t + 1])) / c[t + 1]
        g = a * b
        return g / g.sum(1, keepdims=True)

    def fit(self, x, iters=200, seed=0, tol=1e-8):
        x = np.asarray(x, float)
        rng = np.random.default_rng(seed)
        q = np.sort(rng.choice(x.std() * np.linspace(0.5, 2.0, self.k), self.k, replace=False))
        self.mu, self.sd = np.full(self.k, x.mean()), q
        off = 0.05 / max(self.k - 1, 1)
        self.P = np.full((self.k, self.k), off) + np.eye(self.k) * (0.95 - off)
        self.pi = np.full(self.k, 1.0 / self.k)
        last = -np.inf
        for _ in range(iters):
            a, c, B = self._forward(x)
            b = np.ones((len(x), self.k))
            for t in range(len(x) - 2, -1, -1):
                b[t] = (self.P @ (B[t + 1] * b[t + 1])) / c[t + 1]
            g = a * b
            g /= g.sum(1, keepdims=True)
            xi = (a[:-1, :, None] * self.P[None] * (B[1:] * b[1:])[:, None, :]) / c[1:, None, None]
            self.pi = g[0]
            self.P = xi.sum(0) / xi.sum(0).sum(1, keepdims=True)
            w = g.sum(0)
            self.mu = (g * x[:, None]).sum(0) / w
            self.sd = np.sqrt((g * (x[:, None] - self.mu) ** 2).sum(0) / w)
            ll = float(np.log(c).sum())
            if ll - last < tol:
                break
            last = ll
        order = np.argsort(self.sd)                                    # state 0 = calmest
        self.mu, self.sd, self.pi = self.mu[order], self.sd[order], self.pi[order]
        self.P = self.P[np.ix_(order, order)]
        self.loglik = last
        return self

    def viterbi(self, x):
        x = np.asarray(x, float)
        lB = np.log(self._dens(x) + 1e-300)
        lP = np.log(self.P)
        d = np.log(self.pi + 1e-300) + lB[0]
        back = np.zeros((len(x), self.k), dtype=int)
        for t in range(1, len(x)):
            m = d[:, None] + lP
            back[t] = m.argmax(0)
            d = m.max(0) + lB[t]
        s = np.zeros(len(x), dtype=int)
        s[-1] = int(d.argmax())
        for t in range(len(x) - 1, 0, -1):
            s[t - 1] = back[t, s[t]]
        return s


# ---------------------------------------------------------------------------------------------------- anomalies
def iforest_scores(X, seed=0):
    """Isolation forest (Liu, Ting and Zhou): anomalies are isolated by fewer random splits."""
    from sklearn.ensemble import IsolationForest

    f = IsolationForest(n_estimators=200, random_state=seed, n_jobs=1).fit(X)
    return -f.score_samples(X)


def autoencoder_scores(X, seed=0, hidden=(8, 2, 8)):
    """Reconstruction error of a small autoencoder (a network trained to reproduce its standardised input through a
    two-unit bottleneck)."""
    from sklearn.neural_network import MLPRegressor

    Z = (X - X.mean(0)) / X.std(0)
    ae = MLPRegressor(hidden_layer_sizes=hidden, activation="tanh", max_iter=500, random_state=seed).fit(Z, Z)
    return ((ae.predict(Z) - Z) ** 2).sum(1)
