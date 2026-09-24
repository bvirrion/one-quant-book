"""The binomial model: replication, the whiteboard tree, convergence (Book 5, Chapter 2)."""
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/binomial"))
sys.path.insert(0, str(ROOT / "code/firm/parity"))
from firm_binomial import node_values, params, price  # noqa: E402
from firm_parity import price as black  # noqa: E402

# The whiteboard tree: three steps, up 10 %, down 10 %, 2 % riskless growth per step.
WB = {"spot": 100.0, "strike": 100.0, "u": 1.1, "d": 0.9, "r_step": 1.02, "n": 3}
# The realistic set for convergence: one year, 5 % rate, 20 % volatility, at the money.
REAL = {"spot": 100.0, "strike": 100.0, "t": 1.0, "r": 0.05, "vol": 0.20}


def one_period(s: float, su: float, sd: float, gross: float, vu: float, vd: float) -> dict[str, float]:
    """Replicate a claim paying (vu, vd) with shares and a bond: delta, bond holding, price, q_up."""
    delta = (vu - vd) / (su - sd)
    bond = (vu - delta * su) / gross          # cash invested today, growing to vu - delta*su
    p = (gross * s - sd) / (su - sd)
    return {"delta": delta, "bond": bond, "price": delta * s + bond, "p": p}


def whiteboard() -> dict[str, float]:
    w = WB
    p = (w["r_step"] - w["d"]) / (w["u"] - w["d"])
    _, call = node_values(w["spot"], w["strike"], w["r_step"], w["u"], w["d"], w["n"], "C")
    shares, put = node_values(w["spot"], w["strike"], w["r_step"], w["u"], w["d"], w["n"], "P")
    _, am_put = node_values(w["spot"], w["strike"], w["r_step"], w["u"], w["d"], w["n"], "P", american=True)
    first = one_period(w["spot"], shares[1][1], shares[1][0], w["r_step"], call[1][1], call[1][0])
    digital = sum(math.comb(3, j) * p ** j * (1 - p) ** (3 - j) for j in range(4)
                  if shares[3][j] > w["strike"]) / w["r_step"] ** 3
    return {"p": p, "call": call[0][0], "put": put[0][0], "am_put": am_put[0][0],
            "premium": am_put[0][0] - put[0][0], "delta0": first["delta"], "bond0": first["bond"],
            "parity": call[0][0] - put[0][0], "parity_rhs": w["spot"] - w["strike"] / w["r_step"] ** 3,
            "digital": digital, "shares": shares, "am_put_nodes": am_put, "put_nodes": put, "call_nodes": call}


def bs_put(r: dict = REAL) -> float:
    fwd = r["spot"] * math.exp(r["r"] * r["t"])
    return black(fwd, r["strike"], r["t"], r["r"], r["vol"], "P")


def error(n: int, method: str, r: dict = REAL, right: str = "P") -> float:
    tree = price(r["spot"], r["strike"], r["t"], r["r"], r["vol"], n, right, method=method)
    return tree - bs_put(r)


def steps_within(tol: float = 0.01, n_max: int = 2000, method: str = "crr") -> int:
    """Smallest n after which the European put stays within tol of Black-Scholes, up to n_max."""
    last_bad = 0
    for n in range(1, n_max + 1):
        if abs(error(n, method)) >= tol:
            last_bad = n
    return last_bad + 1


def american_premium_curve(spots, n: int = 501) -> list[tuple[float, float, float]]:
    out = []
    for s in spots:
        eu = price(s, REAL["strike"], REAL["t"], REAL["r"], REAL["vol"], n, "P", method="lr")
        am = price(s, REAL["strike"], REAL["t"], REAL["r"], REAL["vol"], n, "P", american=True, method="lr")
        out.append((s, eu, am))
    return out


def terminal_law(n: int, r: dict = REAL) -> tuple[np.ndarray, np.ndarray]:
    """Terminal log-returns of the CRR tree and their risk-neutral probabilities."""
    u, d, p = params("crr", r["spot"], r["strike"], r["t"], r["r"], 0.0, r["vol"], n)
    j = np.arange(n + 1)
    x = j * math.log(u) + (n - j) * math.log(d)
    w = np.array([math.comb(n, int(k)) * p ** k * (1 - p) ** (n - k) for k in j])
    return x, w
