"""Chapter 15 of Book 2: FX spot microstructure. A simulated EURUSD stream with informed and
uninformed clients, the reject rates and mark-outs a last-look window produces, and the value an
asymmetric window transfers from clients. All parameters are illustrative."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/lastlook"))
from firm_lastlook import expected_transfer, simulate, tca

SIGMA = 0.01          # bp per sqrt(ms): 0.1 bp over 100 ms, 0.32 bp over a second
HALF = 0.4            # half-spread, bp
INFORMED = 0.10       # share of requests from latency arbitrageurs
EDGE = 0.2            # the move they have seen and the quote has not, bp
THRESHOLD = 0.05      # price-check tolerance, bp
N = 40_000
HOLDS = [0, 10, 25, 50, 100, 200, 500]


def by_hold(policy: str, threshold: float) -> list[tuple[int, dict[str, float]]]:
    return [(h, tca(simulate(N, SIGMA, h, threshold, policy, INFORMED, EDGE, seed=11), HALF)) for h in HOLDS]


def no_last_look() -> dict[str, float]:
    return tca(simulate(N, SIGMA, 0, 0.0, "none", INFORMED, EDGE, seed=11), HALF)


def window(notional_per_day: float = 2e9, hold: float = 100, threshold: float = THRESHOLD,
           days: int = 250) -> dict[str, float]:
    """The weekend problem: what an asymmetric window takes from uninformed clients."""
    per = expected_transfer(SIGMA, hold, threshold, "asymmetric")
    sims = simulate(N, SIGMA, hold, threshold, "asymmetric", seed=5)
    sim_per = sum(r.move_at_decision for r in sims if not r.accepted) / len(sims)
    sym = simulate(N, SIGMA, hold, threshold, "symmetric", seed=5)
    return {"per_bp": per, "sim_per_bp": sim_per, "daily": per * 1e-4 * notional_per_day,
            "yearly": per * 1e-4 * notional_per_day * days,
            "reject_asym": sum(not r.accepted for r in sims) / len(sims),
            "reject_sym": sum(not r.accepted for r in sym) / len(sym),
            "sym_kept": sum(r.move_at_decision for r in sym if not r.accepted) / len(sym),
            "per_bp_t0": expected_transfer(SIGMA, hold, 0.0, "asymmetric"),
            "per_bp_h25": expected_transfer(SIGMA, 25, threshold, "asymmetric"),
            "sd_hold": SIGMA * hold ** 0.5,
            "p_reject_asym": 0.5 * math.erfc(threshold / (SIGMA * math.sqrt(hold)) / math.sqrt(2)),
            "p_reject_sym": math.erfc(threshold / (SIGMA * math.sqrt(hold)) / math.sqrt(2)),
            "spread_cost_daily": HALF * 1e-4 * notional_per_day}
