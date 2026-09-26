"""Chapter 21 helpers: the cancel-fill race in closed form, and the simulator runs behind the chapter's figure.

race_exact(lam, L, hold, d)   probability that a cancel meets a fill (a race), for Poisson fills at rate lam (a
                              second) on a resting order, one-way latency L to the venue, report delay d back, and an
                              exponential holding time of mean `hold` before the strategy cancels (all in seconds)
race_rested(lam, L, d)        the same for an order that has rested at least L + d when cancelled:
                              1 - exp(-lam (L + d))
simulate(L_ns, seeds, ...)    fraction of cancels that met a fill in firm.ordergw's runs against Book 10's engine
"""
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "code/firm/ordergw"))
import firm_ordergw as gw  # noqa: E402,F401
import firm_ordergw_sim as sim  # noqa: E402

D = sim.OUT_NS * 1e-9          # the simulator's report delay, 20 us
LAM, HOLD = 200.0, 1e-3        # the figure's fill intensity and mean holding time


def race_rested(lam, L, d=D):
    return 1 - math.exp(-lam * (L + d))


def race_exact(lam, L, hold, d=D):
    """A fill at the venue races the cancel if it happens after the order arrives, before the cancel arrives, and
    late enough that its report reaches the strategy only after the cancel was sent: a window of min(h, L + d) for a
    holding time h. Conditioning on the strategy still cancelling (no fill reported before it decided), with
    a = 1/hold and W = L + d:
        P = [1 - e^{-aW} - a/(a+lam) (1 - e^{-(a+lam)W}) + (1 - e^{-lam W}) a e^{-aW}/(a+lam)]
            / [1 - e^{-aW} + a e^{-aW}/(a+lam)].
    It is below 1 - e^{-lam W} because some cancels come before the order has rested W; as the holding time grows,
    P -> lam W / (1 + lam W) (the orders still there to cancel are the ones that happened not to fill)."""
    a, w = 1 / hold, L + d
    ea = math.exp(-a * w)
    num = 1 - ea - a / (a + lam) * (1 - math.exp(-(a + lam) * w)) + (1 - math.exp(-lam * w)) * a * ea / (a + lam)
    den = 1 - ea + a * ea / (a + lam)
    return num / den


def simulate(L_ns, seeds=(1, 2), cycles=2000, lam=LAM, hold=HOLD):
    """Races per cancel over several seeded runs of the gateway against the matching engine."""
    races = cancels = 0
    for s in seeds:
        r = sim.run(s, L_ns, lam, cycles, hold_ns=int(hold * 1e9))
        races += r.gateway.races
        cancels += r.cancels
    return races, cancels


def expected_races_per_day(cancels, lam, L, d=D):
    return cancels * race_rested(lam, L, d)
