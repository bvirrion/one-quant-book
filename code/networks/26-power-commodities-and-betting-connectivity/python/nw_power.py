"""Chapter 26 of One Quant Book 14: the last megawatt across the border, and polling a betting exchange.
(firm.powerlink)

    RIVALS                     five other participants' latencies to the shared order book (assumptions)
    share_curve(ours, slots)   our share of scarce-capacity events against our median latency
    value(latency_ms, slots)   expected spread captured per MWh offered, at SPREAD_EUR_MWH (assumption)
    polling()                  requests a second and staleness for polling 1,000 markets, by projection
    transactions()             a quoting strategy's transactions above the hourly threshold
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code" / "firm" / "powerlink"))
import firm_powerlink as pl  # noqa: E402

P = pl.Participant
RIVALS = (P("rival 5 ms", 5.0), P("rival 10 ms", 10.0), P("rival 20 ms", 20.0), P("rival 40 ms", 40.0),
          P("rival 80 ms", 80.0))
GRID = tuple(round(10 ** (i / 4), 3) for i in range(0, 9))     # 1 ms to 100 ms, four points a decade
SPREAD_EUR_MWH = 12.0


def share(latency_ms, slots=1):
    return pl.capacity_race((P("us", latency_ms),) + RIVALS, slots)["us"]


def share_curve(slots=1, grid=GRID):
    return [share(m, slots) for m in grid]


def value(latency_ms, slots=1):
    return share(latency_ms, slots) * SPREAD_EUR_MWH


def polling(markets=1000, hz=5, rtt_ms=10.0):
    w = pl.load_weights()
    return {p: {"per_request": pl.markets_per_request(w[p]), "requests_s": pl.poll_requests_per_s(markets, w[p], hz),
                "stale_ms": pl.poll_staleness_ms(hz, rtt_ms)} for p in ("EX_BEST_OFFERS", "EX_ALL_OFFERS+EX_TRADED")}


def transactions(markets=30, changes_per_min=4):
    per_hour = markets * changes_per_min * 60
    return per_hour, pl.charged_transactions(per_hour)
