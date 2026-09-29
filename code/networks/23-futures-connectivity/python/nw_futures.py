"""Chapter 23 of One Quant Book 14: sessions, gateways and the fairness of a race (firm.gwmodel, labelled simulation).

    PARALLEL, SEGMENT          the two gateway designs, parameters as stated assumptions
    curves()                   win rate, winning arrival and a bystander's latency against the firm's sessions k:
                               the firm alone multiplies, everyone multiplies, and the segment design
    marginal(curve)            the monthly value of the k-th session, RACES races a month at VALUE_EUR a race won
    last_paying(curve, fees)   the last session whose value covers its fee (the first session is owned anyway)
    FULL, ULTRA                the exchange's high-frequency session types (dated rows)
"""
import functools
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code" / "firm" / "gwmodel"))
import firm_gwmodel as gm  # noqa: E402

PARALLEL = gm.Design()
SEGMENT = gm.Design(kind="segment")
K = tuple(range(1, 13))
OTHERS, N = 9, 20000
RACES, VALUE_EUR = 20000, 0.5            # races a month and the value of winning one (assumptions)
FULL, ULTRA = gm.load_sessions()


@functools.cache
def curves():
    solo = [gm.win_rate(PARALLEL, k, OTHERS, 1, N) for k in K]
    everyone = [gm.win_rate(PARALLEL, k, OTHERS, k, N) for k in K]
    segment = [gm.win_rate(SEGMENT, k, OTHERS, 1, N) for k in K]
    return {"solo": solo, "everyone": everyone, "segment": segment}


def marginal(curve):
    p = [c[0] for c in curve]
    return [(k, (p[i] - p[i - 1]) * RACES * VALUE_EUR) for i, k in enumerate(K) if i > 0]


def fee(k):
    """The monthly fee of the k-th Full session under the dated schedule."""
    return FULL.fee_first if k <= FULL.first_n else FULL.fee_after


def last_paying(curve):
    last = 1
    for k, v in marginal(curve):
        if v >= fee(k):
            last = k
        else:
            break
    return last
