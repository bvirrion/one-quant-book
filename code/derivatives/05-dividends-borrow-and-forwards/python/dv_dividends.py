"""Dividends, borrow and forwards: three dividend models, a forward curve read from a chain, and a
hard-to-borrow share (Book 5, Chapter 5)."""
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for comp in ("bs", "divfwd"):
    sys.path.insert(0, str(ROOT / f"code/firm/{comp}"))
from firm_bs import black, bs, implied_vol  # noqa: E402
from firm_divfwd import ForwardCurve, implied_borrow, implied_carry, implied_forward, strip_dividends  # noqa: E402

# ---------------------------------------------------------------- three models, one dividend
ONE = {"spot": 100.0, "t": 1.0, "r": 0.03, "vol": 0.25, "div": 4.0, "t_div": 0.5}


def escrowed_call(k: float, c: dict = ONE) -> float:
    """Escrowed model: S - PV(D) is lognormal with the quoted volatility."""
    pv = c["div"] * math.exp(-c["r"] * c["t_div"])
    return bs(c["spot"] - pv, k, c["t"], c["r"], 0.0, c["vol"], "C")


def forward(c: dict = ONE) -> float:
    return (c["spot"] - c["div"] * math.exp(-c["r"] * c["t_div"])) * math.exp(c["r"] * c["t"])


def proportional_call(k: float, c: dict = ONE) -> float:
    """Proportional model: the dividend is a fraction of the share, so the share is lognormal
    throughout; with the same forward this is Black's formula at the quoted volatility."""
    return black(forward(c), k, c["t"], math.exp(-c["r"] * c["t"]), c["vol"], "C")


def spot_call(k: float, c: dict = ONE, n: int = 96) -> float:
    """Spot model: the share is lognormal with the quoted volatility and drops by the cash amount on the
    ex-date. Condition on the share just before the ex-date (Gauss-Hermite in its log) and price the
    remaining period with Black-Scholes."""
    x, w = np.polynomial.hermite_e.hermegauss(n)          # nodes and weights for exp(-x^2/2)
    w = w / w.sum()
    t1, s0, r, v = c["t_div"], c["spot"], c["r"], c["vol"]
    s1 = s0 * np.exp((r - 0.5 * v * v) * t1 + v * math.sqrt(t1) * x)
    after = np.maximum(s1 - c["div"], 1e-12)
    vals = np.array([bs(s, k, c["t"] - t1, r, 0.0, v, "C") for s in after])
    return float(math.exp(-r * t1) * (w * vals).sum())


def effective_vol(c: dict = ONE) -> float:
    """Volatility to give the escrowed share S* = S - PV(D) so that it matches the spot model: before the
    ex-date S* carries the whole share's moves, so its volatility is sigma S / S*."""
    pv = c["div"] * math.exp(-c["r"] * c["t_div"])
    ratio = c["spot"] / (c["spot"] - pv)
    return c["vol"] * math.sqrt((ratio ** 2 * c["t_div"] + (c["t"] - c["t_div"])) / c["t"])


def model_smiles(strikes) -> list[tuple[float, float, float, float]]:
    """Implied volatility (Black on the common forward) by strike of: the escrowed and the proportional
    models at the quoted volatility (identical), the spot model, and the escrowed model at the
    effective volatility."""
    f, df = forward(), math.exp(-ONE["r"] * ONE["t"])
    adj = {**ONE, "vol": effective_vol()}
    out = []
    for k in strikes:
        vols = [implied_vol(p, f, k, ONE["t"], df, "C")
                for p in (escrowed_call(k), spot_call(k), escrowed_call(k, adj))]
        out.append((k, *vols))
    return out


# ---------------------------------------------------------------- a forward curve from a chain
CURVE = ForwardCurve(spot=100.0, rate=0.03, cash=tuple((0.1 + 0.25 * i, 0.60) for i in range(8)), borrow=0.005)
EXPIRIES = tuple(0.25 * i for i in range(1, 9))
STRIKES = tuple(float(k) for k in range(80, 121, 5))


def chain_vol(k: float, t: float, f: float) -> float:
    return 0.20 - 0.10 * math.log(k / f) / math.sqrt(max(t, 0.25))


def synthetic_chain(seed: int = 7, noise: float = 0.02):
    """Mid prices of European calls and puts on the curve, with rounding noise."""
    rng = np.random.default_rng(seed)
    out = []
    for t in EXPIRIES:
        f, df = CURVE.forward(t), CURVE.df(t)
        calls = [black(f, k, t, df, chain_vol(k, t, f), "C") + noise * rng.uniform(-1, 1) for k in STRIKES]
        puts = [black(f, k, t, df, chain_vol(k, t, f), "P") + noise * rng.uniform(-1, 1) for k in STRIKES]
        out.append((t, calls, puts))
    return out


def curve_from_chain(seed: int = 7) -> list[dict]:
    rows = []
    fwds, dfs = [], []
    for t, calls, puts in synthetic_chain(seed):
        f, df = implied_forward(STRIKES, calls, puts)
        fwds.append(f)
        dfs.append(df)
        rows.append({"t": t, "fwd": f, "fwd_true": CURVE.forward(t), "df": df, "rate": -math.log(df) / t,
                     "carry": implied_carry(CURVE.spot, f, df),
                     "carry_true": implied_carry(CURVE.spot, CURVE.forward(t), CURVE.df(t))})
    true_steps = strip_dividends(CURVE.spot, EXPIRIES, [CURVE.forward(t) for t in EXPIRIES],
                                 [CURVE.df(t) for t in EXPIRIES])
    for row, d, d0 in zip(rows, strip_dividends(CURVE.spot, EXPIRIES, fwds, dfs), true_steps, strict=True):
        row["carry_step"], row["carry_step_true"] = d, d0
    return rows


# ---------------------------------------------------------------- the hard-to-borrow share
HTB = {"spot": 50.0, "t": 30 / 365, "r": 0.04, "borrow": 0.35, "vol": 0.60}
HTB_STRIKES = (45.0, 47.5, 50.0, 52.5, 55.0)


def htb_chain() -> list[tuple[float, float, float]]:
    """Mid quotes (rounded to the cent) of one-month calls and puts on a share that costs 35 % to borrow."""
    c = HTB
    f = c["spot"] * math.exp((c["r"] - c["borrow"]) * c["t"])
    df = math.exp(-c["r"] * c["t"])
    return [(k, round(black(f, k, c["t"], df, c["vol"], "C"), 2), round(black(f, k, c["t"], df, c["vol"], "P"), 2))
            for k in HTB_STRIKES]


def htb_results() -> dict[str, float]:
    c = HTB
    chain = htb_chain()
    f, df = implied_forward([k for k, _, _ in chain], [x for _, x, _ in chain], [p for _, _, p in chain])
    naive_f = c["spot"] * math.exp(c["r"] * c["t"])
    call_mkt = dict((k, x) for k, x, _ in chain)[50.0]
    put_mkt = dict((k, p) for k, _, p in chain)[50.0]
    call_naive = black(naive_f, 50.0, c["t"], math.exp(-c["r"] * c["t"]), c["vol"], "C")
    put_naive = black(naive_f, 50.0, c["t"], math.exp(-c["r"] * c["t"]), c["vol"], "P")
    return {"fwd": f, "df": df, "rate": -math.log(df) / c["t"], "carry": implied_carry(c["spot"], f, df),
            "borrow": implied_borrow(c["spot"], f, df, c["t"]), "naive_fwd": naive_f,
            "call_mkt": call_mkt, "put_mkt": put_mkt, "call_naive": call_naive, "put_naive": put_naive,
            "call_err": call_naive - call_mkt, "put_err": put_naive - put_mkt,
            "iv_call_naive": implied_vol(call_mkt, naive_f, 50.0, c["t"], math.exp(-c["r"] * c["t"]), "C"),
            "iv_put_naive": implied_vol(put_mkt, naive_f, 50.0, c["t"], math.exp(-c["r"] * c["t"]), "P"),
            "reversal_edge": call_mkt - put_mkt - (c["spot"] - 50.0 * math.exp(-c["r"] * c["t"]))}
