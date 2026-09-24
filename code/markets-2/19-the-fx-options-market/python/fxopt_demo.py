"""Chapter 19 of Book 2: the FX options market. Three-month EURUSD and USDJPY smiles built from
at-the-money, risk-reversal and butterfly quotes under different delta conventions, and the hedge a
desk short a EURUSD down-and-out call must unwind at the barrier. Rates are converted from the
simple money-market rates of Chapter 16; volatility quotes and the barrier trade are illustrative."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/fxsmile"))
from firm_fxsmile import (
    atm_dns,
    barrier_delta,
    delta,
    down_and_out_call,
    forward,
    gk,
    quadratic_smile,
    smile_vols,
    strike_from_delta,
)

T = 0.25


def cc(simple: float, t: float = T) -> float:
    """Continuously compounded equivalent of a simple rate over t."""
    return math.log(1 + simple * t) / t


R_USD, R_EUR, R_JPY = cc(0.0368), cc(0.02), cc(0.00977)
EURUSD = {"s": 1.1464, "rd": R_USD, "rf": R_EUR, "atm": 0.070, "rr": -0.005, "bf": 0.002}
USDJPY = {"s": 156.87, "rd": R_JPY, "rf": R_USD, "atm": 0.095, "rr": -0.012, "bf": 0.003}


def smile(m: dict[str, float], kind: str, pa_atm: bool) -> dict[str, float]:
    c, p = smile_vols(m["atm"], m["rr"], m["bf"])
    kc = strike_from_delta(m["s"], T, m["rd"], m["rf"], c, 0.25, 1, kind)
    kp = strike_from_delta(m["s"], T, m["rd"], m["rf"], p, -0.25, -1, kind)
    ka = atm_dns(m["s"], T, m["rd"], m["rf"], m["atm"], pa_atm)
    return {"vol_c": c, "vol_p": p, "k_c": kc, "k_p": kp, "k_atm": ka,
            "fwd": forward(m["s"], T, m["rd"], m["rf"])}


def smile_curve(m: dict[str, float], kind: str, pa_atm: bool, n: int = 41) -> list[tuple[float, float]]:
    sm = smile(m, kind, pa_atm)
    f = quadratic_smile([(sm["k_p"], sm["vol_p"]), (sm["k_atm"], m["atm"]), (sm["k_c"], sm["vol_c"])])
    lo, hi = sm["k_p"] * 0.97, sm["k_c"] * 1.03
    return [(lo + (hi - lo) * i / (n - 1), f(lo + (hi - lo) * i / (n - 1))) for i in range(n)]


# ---- the barrier ------------------------------------------------------------------------------
K, B, NOTIONAL, VOL = 1.1464, 1.1200, 500e6, 0.07


def barrier() -> dict[str, float]:
    m = EURUSD
    near = 1.1201
    return {"vanilla": gk(m["s"], K, T, m["rd"], m["rf"], VOL),
            "ko": down_and_out_call(m["s"], K, B, T, m["rd"], m["rf"], VOL),
            "delta_now": barrier_delta(m["s"], K, B, T, m["rd"], m["rf"], VOL),
            "delta_near": barrier_delta(near, K, B, T, m["rd"], m["rf"], VOL),
            "vanilla_delta_near": delta(near, K, T, m["rd"], m["rf"], VOL),
            "sell_at_barrier": barrier_delta(near, K, B, T, m["rd"], m["rf"], VOL) * NOTIONAL}


def barrier_curve(n: int = 61) -> list[tuple[float, float, float]]:
    m = EURUSD
    out = []
    for i in range(n):
        s = 1.10 + 0.07 * i / (n - 1)
        out.append((s, down_and_out_call(s, K, B, T, m["rd"], m["rf"], VOL) * 1e4,
                    barrier_delta(s, K, B, T, m["rd"], m["rf"], VOL) if s > B + 1e-4 else 0.0))
    return out


def delta_curves(n: int = 81) -> list[tuple[float, float, float]]:
    """(strike, regular spot call delta, premium-adjusted spot call delta) for USDJPY at 9.5%."""
    m, out = USDJPY, []
    for i in range(n):
        k = 120.0 + 80.0 * i / (n - 1)
        out.append((k, delta(m["s"], k, T, m["rd"], m["rf"], m["atm"], 1, "spot"),
                    delta(m["s"], k, T, m["rd"], m["rf"], m["atm"], 1, "spot_pa")))
    return out
