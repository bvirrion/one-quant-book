"""Chapter 10 of Book 6: modelling overnight-rate products. Backward-looking caplets on three-month
compounded SOFR against forward-looking (term-rate) caplets, on chapter 1's SOFR curve with Hull-White
(kappa 3%, sigma 90 bp); the in-period variance; the generalised forward market model's decay; and a
meeting-date view of the same period with the Federal Reserve's 2026-2027 meeting calendar."""
import datetime as dt
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
for p in ("code/firm/rfrcaplet", "code/rates-credit-risk/01-curve-construction/python"):
    sys.path.insert(0, str(ROOT / p))
import rc_curves as rc  # noqa: E402
from firm_rfrcaplet import (  # noqa: E402
    gfmm_effective_variance,
    hw_backward_caplet,
    hw_backward_caplet_mc,
    hw_forward_caplet,
    hw_period_variances,
    meeting_variance,
)

CURVE = rc.curves()["monotone_convex"].curve
SPOT = rc.SPOT
KAPPA, SIGMA = 0.03, 0.0090
STRIKE = 0.0375
PERIODS = [(0.25 * i, 0.25 * (i + 1)) for i in range(8)]          # two years of quarterly periods
# FOMC decision days (second day of each meeting), 2026-2027, as years from SPOT
FOMC = [dt.date(2026, 10, 28), dt.date(2026, 12, 9), dt.date(2027, 1, 27), dt.date(2027, 3, 17),
        dt.date(2027, 4, 28), dt.date(2027, 6, 9), dt.date(2027, 7, 28), dt.date(2027, 9, 15),
        dt.date(2027, 10, 27), dt.date(2027, 12, 8)]
MEETINGS = [(d - SPOT).days / 365.0 for d in FOMC]


def forward(S: float, E: float) -> float:
    return (CURVE.df_t(S) / CURVE.df_t(E) - 1) / (E - S)


def cap_table(notional: float = 1e8) -> list[tuple]:
    """Per period: (S, E, forward %, backward caplet, forward caplet, in-period share of variance %)."""
    rows = []
    for S, E in PERIODS:
        b, d = hw_period_variances(KAPPA, SIGMA, S, E)
        rows.append((S, E, 100 * forward(S, E), notional * hw_backward_caplet(CURVE, KAPPA, SIGMA, S, E, STRIKE),
                     notional * (hw_forward_caplet(CURVE, KAPPA, SIGMA, S, E, STRIKE) if S > 0 else 0.0),
                     100 * d / (b + d)))
    return rows


def cap_totals(notional: float = 1e8) -> dict[str, float]:
    t = cap_table(notional)
    back, fwd = sum(r[3] for r in t), sum(r[4] for r in t)
    return {"backward": back, "forward": fwd, "gap": back - fwd, "first": t[0][3]}


def mc_check(S: float = 1.0, E: float = 1.25) -> tuple[float, float, float]:
    mc, se = hw_backward_caplet_mc(CURVE, KAPPA, SIGMA, S, E, STRIKE)
    return hw_backward_caplet(CURVE, KAPPA, SIGMA, S, E, STRIKE), mc, se


def remaining_sd_profile(S: float = 1.0, E: float = 1.25, jump_sd: float | None = None):
    """(t, GFMM remaining sd %, meeting-model remaining sd %) of the period's rate, both scaled to
    the same total at t = 0 (the meeting jumps' size is chosen to match)."""
    g0 = gfmm_effective_variance(1.0, S, E, 0.0)
    m0 = meeting_variance(MEETINGS, 1.0, S, E, 0.0)
    rows = []
    for i in range(0, 126):
        t = i * 0.01
        g = gfmm_effective_variance(1.0, S, E, t) / g0
        mv = meeting_variance(MEETINGS, 1.0, S, E, t) / m0
        rows.append((t, 100 * g**0.5, 100 * mv**0.5))
    return rows


def meetings_in(S: float, E: float) -> list[float]:
    return [m for m in MEETINGS if S < m < E]
