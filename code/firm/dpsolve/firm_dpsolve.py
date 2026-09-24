"""firm.dpsolve -- finite-horizon dynamic programming on grids (One Quant Book 4, chapters 9-10).

Backward induction V_t(x) = max_u { r(t, x, u) + E[ V_{t+1}(X_{t+1}) | X_t = x, u ] } on a state
grid, with the expectation taken over a finite set of next states (quadrature nodes and weights)
and V_{t+1} interpolated linearly between grid points (flat beyond the ends).

API (stable):
    backward_induction(grid, controls, n_steps, reward, transition, terminal, stop=None)
        grid        1-D increasing array of states
        controls    1-D array of admissible controls
        reward      reward(t, x, u) -> array broadcast over (states, controls)
        transition  transition(t, x, u) -> (next_states, weights), next_states shaped
                    (states, controls, nodes), weights shaped (nodes,)
        terminal    terminal(x) -> array over the grid
        stop        optional stop(t, x) -> reward from stopping now (optimal stopping, chapter 10)
    returns dict(values: (n_steps + 1, states), policy: (n_steps, states), stop: bool array or None)
    gauss_hermite_normal(n) -> nodes and weights for E[f(Z)], Z ~ N(0, 1)
"""
from __future__ import annotations

import numpy as np


def gauss_hermite_normal(n: int) -> tuple[np.ndarray, np.ndarray]:
    """Nodes z_k and weights w_k with sum_k w_k f(z_k) ~ E[f(Z)] for a standard normal Z."""
    x, w = np.polynomial.hermite.hermgauss(n)
    return np.sqrt(2.0) * x, w / np.sqrt(np.pi)


def backward_induction(grid, controls, n_steps: int, reward, transition, terminal, stop=None) -> dict:
    grid = np.asarray(grid, dtype=float)
    controls = np.asarray(controls, dtype=float)
    values = np.empty((n_steps + 1, grid.size))
    policy = np.empty((n_steps, grid.size))
    stopped = np.zeros((n_steps, grid.size), dtype=bool) if stop is not None else None
    values[n_steps] = terminal(grid)
    X, U = np.meshgrid(grid, controls, indexing="ij")
    for t in range(n_steps - 1, -1, -1):
        nxt, w = transition(t, X, U)
        cont = np.interp(nxt, grid, values[t + 1]) @ w           # (states, controls)
        total = reward(t, X, U) + cont
        best = np.argmax(total, axis=1)
        values[t] = total[np.arange(grid.size), best]
        policy[t] = controls[best]
        if stop is not None:
            s = stop(t, grid)
            stopped[t] = s >= values[t]
            values[t] = np.maximum(values[t], s)
    return {"values": values, "policy": policy, "stop": stopped}
