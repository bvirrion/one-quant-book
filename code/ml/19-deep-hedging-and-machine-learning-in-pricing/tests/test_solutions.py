"""Numbers gate: every numerical answer printed in Book 12, chapter 19 (text and solutions). Trains five hedging
networks, six surrogates and a calibration network (about two and a half minutes on one core)."""
import math
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import ml_hedge as m  # noqa: E402


def test_setup():
    assert (round(m.price(), 2), round(m.vega_point(), 3), round(100 * m.atm_vol(), 2)) == (2.25, 0.115, 19.58)
    bs_cost, deep_cost = m.turnover()
    assert (round(bs_cost, 3), round(deep_cost, 3)) == (0.123, 0.099) and bs_cost > m.vega_point()


# Printed digits that move with the CPU's floating-point kernels: skipped by CI (make test-fast).
@pytest.mark.reference
def test_hedging():
    h = m.hedging()
    ind = {c: tuple(round(h[c][k]["entropic"], 3) for k in ("deep hedge", "Black-Scholes delta", "Whalley-Wilmott"))
           for c in m.COSTS}
    assert ind == {0.0: (2.454, 2.475, 2.475), 0.0005: (2.558, 2.608, 2.606), 0.001: (2.658, 2.743, 2.712),
                   0.002: (2.840, 3.018, 2.910)}
    ten = {k: tuple(round(v, 3) for v in h[0.001][k].values()) for k in ("deep hedge", "Whalley-Wilmott",
                                                                        "Black-Scholes delta", "no hedge")}
    assert ten == {"deep hedge": (2.658, 3.817, 2.442, 0.643), "Whalley-Wilmott": (2.712, 4.044, 2.424, 0.703),
                   "Black-Scholes delta": (2.743, 4.090, 2.507, 0.595), "no hedge": (8.767, 9.992, 2.235, 2.945)}
    widths = {c: (round(h[c]["band deep"][1] - h[c]["band deep"][0], 3), round(h[c]["band WW"][1] - h[c]["band WW"][0], 3))
              for c in m.COSTS}
    assert widths[0.0005] == (0.031, 0.181) and widths[0.002] == (0.104, 0.288) and widths[0.001] == (0.055, 0.229)
    assert round(2.454 - 2.254, 2) == 0.20
    lo, hi = h[0.0]["band deep"]
    assert (lo + hi) / 2 < h[0.0]["band WW"][0]                        # the learned hedge ratio is below the BS delta


def test_bands_wider_below_the_money_narrower_above():
    net, ww = m.hedger(m.COSTS[-1]), m.ww_policy(m.atm_vol(), m.K, m.T, m.COSTS[-1], 1.0)
    dl, dh = m.band(net, 0.5, 92.0, m.K)
    wl, wh = m.band(ww, 0.5, 92.0, m.K)
    assert dh - dl > wh - wl
    dl, dh = m.band(net, 0.5, 106.0, m.K)
    wl, wh = m.band(ww, 0.5, 106.0, m.K)
    assert dh - dl < wh - wl


# Printed digits that move with the CPU's floating-point kernels: skipped by CI (make test-fast).
@pytest.mark.reference
def test_shortfall():
    s = m.shortfall_hedge()
    got = {k: (round(v["entropic"], 3), round(v["ES"], 3), round(v["mean cost"], 3), round(v["sd"], 3))
           for k, v in s.items() if k != "band ES"}
    assert got == {"ES-trained": (2.671, 3.763, 2.457, 0.657), "entropic-trained": (2.658, 3.817, 2.442, 0.643)}


def test_surrogates():
    s = {k: tuple(round(x, 3) for x in v) for k, v in m.surrogates().items()}
    assert s == {(256, False): (0.927, 0.066), (256, True): (0.679, 0.057), (1024, False): (0.436, 0.059),
                 (1024, True): (0.218, 0.021), (4096, False): (0.297, 0.042), (4096, True): (0.279, 0.020)}


# Printed digits that move with the CPU's floating-point kernels: skipped by CI (make test-fast).
@pytest.mark.reference
def test_calibration():
    c = m.calibration()
    e = {k: round(100 * v, 1) for k, v in c["parameter rmse / range"].items()}
    assert e == {"v0": 1.7, "kappa": 18.7, "vbar": 9.7, "eta": 9.0, "rho": 9.8}
    assert round(c["price rmse (bp of spot)"], 1) == 13.2
    lm = m.lm_check(5)
    assert round(float(np.mean([x[0] for x in lm])), 2) == 0.46 and max(max(x[1], x[2]) for x in lm) < 1e-6


def test_exercises():
    tau = m.T / 2
    d1 = 0.5 * m.atm_vol() * math.sqrt(tau)
    g = math.exp(-0.5 * d1 * d1) / math.sqrt(2 * math.pi) / (100 * m.atm_vol() * math.sqrt(tau))
    assert round(g, 4) == 0.0998
    assert (round(1.5 * 0.001 * 100 * g * g, 6), round((1.5 * 0.001 * 100 * g * g) ** (1 / 3), 3)) == (0.001494, 0.114)
