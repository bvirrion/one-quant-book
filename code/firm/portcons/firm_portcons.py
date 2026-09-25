"""firm.portcons -- portfolio construction over firm.portopt (build of One Quant Book 7, chapter 25).

Mean-variance construction of a book from an alpha forecast (chapter 15) and a factor risk model (chapter 24):
    maximise alpha'w - gamma/2 w'(X F X' + D)w - kappa |w - w0|_1
    subject to equalities a_k'w = b_k (budget, dollar, beta and factor neutrality), per-name bounds lo <= w <= hi
    (name limits, liquidity limits, long-only), a gross limit |w|_1 <= G and a turnover limit |w - w0|_1 <= T,
solved as one quadratic programme by firm.portopt.qp (split variables for the absolute values are added only when a
gross or turnover term is present). The result carries each named constraint's shadow price (the rate at which the
objective improves per unit of relaxation), the binding constraints, the ex-ante information ratio and the trade
list. NumPy only.

API (stable):
    Problem(alpha, X, F, spec, gamma, w0)       the objective; X (n, K) exposures, F (K, K), spec (n,) variances
    .equality(row, value, name)                 a'w = value (budget: ones; dollar-neutral: ones, 0; beta: betas, 0)
    .neutral_factors(cols, names)               X[:, k]'w = 0 for each listed factor column
    .bounds(lo, hi, name)                       per-name bounds (scalars or arrays; intersected if called twice)
    .liquidity(adv, participation, capital, name)  |w_i| <= participation * adv_i / capital
    .gross(limit, name), .turnover(limit, name), .turnover_penalty(kappa)
    .solve(tol) -> dict(w, objective, alpha, risk, ir, gross, turnover, duals {name: shadow price},
                        binding {name: count}, pull {name: (n,) shadow-price vector in w}, status)
    .ir_decomposition(result)                   {'ir_free', 'ir_eff', 'delta' {name: share of IR^2 it removes}}
    ir_ex_ante(alpha, Sigma, w)                 alpha'w / sqrt(w'Sigma w)
    trade_list(w, w0, capital, prices, names)   [(name, shares)] rounded to whole shares, largest first
"""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "portopt"))
from firm_portopt import qp  # noqa: E402


class Problem:
    def __init__(self, alpha, X, F, spec, gamma: float, w0=None):
        self.alpha = np.asarray(alpha, float)
        self.n = len(self.alpha)
        self.X, self.F = np.asarray(X, float), np.asarray(F, float)
        self.Sigma = self.X @ self.F @ self.X.T + np.diag(np.asarray(spec, float))
        self.gamma = float(gamma)
        self.w0 = np.zeros(self.n) if w0 is None else np.asarray(w0, float)
        self.eqs, self.lo, self.hi = [], np.full(self.n, -np.inf), np.full(self.n, np.inf)
        self.bound_name = {}
        self.gross_limit = self.turn_limit = None
        self.kappa = 0.0

    def equality(self, row, value: float = 0.0, name: str = "budget"):
        self.eqs.append((name, np.asarray(row, float), float(value)))

    def neutral_factors(self, cols, names):
        for k, nm in zip(cols, names, strict=True):
            self.equality(self.X[:, k], 0.0, nm)

    def bounds(self, lo, hi, name: str = "name limit"):
        lo = np.broadcast_to(np.asarray(lo, float), (self.n,))
        hi = np.broadcast_to(np.asarray(hi, float), (self.n,))
        tighter_lo, tighter_hi = lo > self.lo, hi < self.hi
        for i in np.flatnonzero(tighter_lo):
            self.bound_name[(i, -1)] = name
        for i in np.flatnonzero(tighter_hi):
            self.bound_name[(i, 1)] = name
        self.lo, self.hi = np.maximum(self.lo, lo), np.minimum(self.hi, hi)

    def liquidity(self, adv, participation: float, capital: float, name: str = "liquidity"):
        cap = participation * np.asarray(adv, float) / capital
        self.bounds(-cap, cap, name)

    def gross(self, limit: float, name: str = "gross"):
        self.gross_limit, self.gross_name = float(limit), name

    def turnover(self, limit: float, name: str = "turnover"):
        self.turn_limit, self.turn_name = float(limit), name

    def turnover_penalty(self, kappa: float):
        self.kappa = float(kappa)

    def solve(self, tol: float = 1e-9) -> dict:
        n = self.n
        use_g = self.gross_limit is not None
        use_t = self.turn_limit is not None or self.kappa > 0
        blocks = 1 + 2 * use_g + 2 * use_t                             # w | a, c (w = a - c) | u, v (w - w0 = u - v)
        N = blocks * n
        P = np.zeros((N, N))
        P[:n, :n] = self.gamma * self.Sigma
        q = np.zeros(N)
        q[:n] = -self.alpha
        A, b, eq_names = [], [], []
        for name, row, val in self.eqs:
            r = np.zeros(N)
            r[:n] = row
            A.append(r)
            b.append(val)
            eq_names.append(name)
        G, h, ineq = [], [], []
        off = n
        if use_g:
            A += list(np.hstack([np.eye(n), -np.eye(n), np.eye(n), np.zeros((n, N - 3 * n))]))
            b += [0.0] * n
            eq_names += ["_glink"] * n
            G.append(np.hstack([np.zeros((2 * n, n)), -np.eye(2 * n), np.zeros((2 * n, N - 3 * n))]))
            h.append(np.zeros(2 * n))
            ineq += ["_nonneg"] * (2 * n)
            G.append(np.concatenate([np.zeros(n), np.ones(2 * n), np.zeros(N - 3 * n)])[None, :])
            h.append([self.gross_limit])
            ineq.append(self.gross_name)
            off = 3 * n
        if use_t:
            A += list(np.hstack([np.eye(n), np.zeros((n, off - n)), -np.eye(n), np.eye(n)]))
            b += list(self.w0)
            eq_names += ["_tlink"] * n
            G.append(np.hstack([np.zeros((2 * n, off)), -np.eye(2 * n)]))
            h.append(np.zeros(2 * n))
            ineq += ["_nonneg"] * (2 * n)
            q[off:] = self.kappa
            if self.turn_limit is not None:
                G.append(np.concatenate([np.zeros(off), np.ones(2 * n)])[None, :])
                h.append([self.turn_limit])
                ineq.append(self.turn_name)
        for side, lim in ((1, self.hi), (-1, self.lo)):
            idx = np.flatnonzero(np.isfinite(lim))
            if len(idx):
                rows = np.zeros((len(idx), N))
                rows[np.arange(len(idx)), idx] = side
                G.append(rows)
                h.append(side * lim[idx])
                ineq += [self.bound_name.get((i, side), "bound") for i in idx]
        Am = np.array(A).reshape(-1, N) if A else None
        bm = np.array(b) if A else None
        Gm = np.vstack(G) if G else np.zeros((0, N))
        hm = np.concatenate([np.atleast_1d(x) for x in h]) if h else np.zeros(0)
        sol = qp(P, q, Am, bm, Gm, hm, tol=tol)
        w = sol["x"][:n]
        duals, binding = {}, {}
        for k, name in enumerate(eq_names):
            if not name.startswith("_"):
                duals[name] = float(sol["y"][k])
        names = np.array(ineq)
        slack = hm - Gm @ sol["x"] if len(hm) else np.zeros(0)
        for name in set(ineq) - {"_nonneg"}:
            m = names == name
            duals[name] = float(np.sum(sol["z"][m]))
            binding[name] = int(np.sum(slack[m] < 1e-6))
        risk = math.sqrt(float(w @ self.Sigma @ w))
        # each named constraint's shadow-price vector in the w block: alpha - gamma Sigma w = sum of these
        pull = {}
        tname = getattr(self, "turn_name", "turnover") if self.turn_limit is not None else "turnover penalty"
        for k, name in enumerate(eq_names):
            key = {"_glink": getattr(self, "gross_name", "gross"), "_tlink": tname}.get(name, name)
            pull[key] = pull.get(key, 0.0) + sol["y"][k] * Am[k, :n]
        for k, name in enumerate(ineq):
            if name != "_nonneg" and Gm[k, :n].any():
                pull[name] = pull.get(name, 0.0) + sol["z"][k] * Gm[k, :n]
        return {"w": w, "objective": -sol["objective"], "alpha": float(self.alpha @ w), "risk": risk,
                "ir": float(self.alpha @ w) / risk if risk > 0 else 0.0, "gross": float(np.abs(w).sum()),
                "turnover": float(np.abs(w - self.w0).sum()), "duals": duals, "binding": binding,
                "pull": {k: np.asarray(v, float) * np.ones(n) for k, v in pull.items()}, "status": sol["status"]}

    def ir_decomposition(self, result: dict) -> dict:
        """The unconstrained IR^2 = alpha' Sigma^-1 alpha minus the constrained one, gamma^2 w' Sigma w, split exactly
        by constraint: for g_k the constraint's shadow-price vector and G their sum (alpha - G = gamma Sigma w),
        delta_k = g_k' Sigma^-1 (2 alpha - G). Returns {'ir_free', 'ir_eff', 'delta': {name: delta_k}}."""
        Si = np.linalg.inv(self.Sigma)
        pull = result["pull"]
        G = sum(pull.values()) if pull else np.zeros(self.n)
        free = float(self.alpha @ Si @ self.alpha)
        delta = {k: float(g @ Si @ (2 * self.alpha - G)) for k, g in pull.items()}
        return {"ir_free": math.sqrt(free), "ir_eff": math.sqrt(max(free - sum(delta.values()), 0.0)), "delta": delta}


def ir_ex_ante(alpha, Sigma, w) -> float:
    w = np.asarray(w, float)
    return float(np.asarray(alpha) @ w / math.sqrt(w @ np.asarray(Sigma) @ w))


def trade_list(w, w0, capital: float, prices, names=None):
    sh = np.round((np.asarray(w) - np.asarray(w0)) * capital / np.asarray(prices, float)).astype(int)
    names = np.arange(len(sh)) if names is None else np.asarray(names)
    order = np.argsort(-np.abs(sh))
    return [(names[i].item() if hasattr(names[i], "item") else names[i], int(sh[i])) for i in order if sh[i] != 0]
