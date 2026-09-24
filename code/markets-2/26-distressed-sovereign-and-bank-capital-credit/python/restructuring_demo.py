"""Chapter 26 of Book 2: distressed, sovereign and bank-capital credit. An illustrative sovereign
exchange offer valued at exit yields, a holdout's probability tree against the participation, with
and without an aggregated collective action clause, and loss absorption in an illustrative bank
capital stack in two orders. All parameters are illustrative; values per 100 of old face value."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/recovery"))
from firm_recovery import Holdout, Offer, absorb, breakeven_participation, holdout_payoff, npv_haircut

EXIT_YIELD = 0.09
OFFER = Offer(new_face=50.0, coupon=0.04, years=15, cash=5.0)
CLAIM_WITH_INTEREST = 130.0                      # face plus past-due interest, recovered by a lawsuit
HOLDOUT = Holdout(paid_soon=100 / (1 + EXIT_YIELD), lawsuit_prob=0.30,
                  lawsuit_pv=CLAIM_WITH_INTEREST / (1 + EXIT_YIELD) ** 6, stuck=15.0)
CAC = 0.75                                       # single-limb aggregated threshold
STACK = [("CET1", 45.0), ("AT1", 16.0), ("Tier 2", 12.0), ("senior bail-in", 80.0)]   # illustrative, bn


def offer_curve(lo: int = 5, hi: int = 15) -> list[tuple[float, float, float]]:
    """(exit yield %, value with cash, value of the new bonds alone)."""
    return [(y / 2, OFFER.value(y / 200), OFFER.value(y / 200) - OFFER.cash) for y in range(2 * lo, 2 * hi + 1)]


def holdout_curve(n: int = 100) -> list[tuple[float, float, float, float]]:
    """(participation %, holdout value with the CAC, without a CAC, tender value)."""
    tender, bound = OFFER.value(EXIT_YIELD), OFFER.value(EXIT_YIELD) - OFFER.cash
    return [(100 * k / n, holdout_payoff(k / n, HOLDOUT, bound, CAC), holdout_payoff(k / n, HOLDOUT, bound, None),
             tender) for k in range(n + 1)]


def tutorial() -> dict[str, float]:
    tender = OFFER.value(EXIT_YIELD)
    p_star = breakeven_participation(HOLDOUT, tender)
    return {"new_bonds": tender - OFFER.cash, "tender": tender, "npv_haircut": npv_haircut(tender),
            "face_haircut": 1 - OFFER.new_face / 100, "value_6": OFFER.value(0.06), "value_12": OFFER.value(0.12),
            "paid_soon": HOLDOUT.paid_soon, "lawsuit_pv": HOLDOUT.lawsuit_pv,
            "h0": HOLDOUT.value(0.0), "h60": HOLDOUT.value(0.60), "h74": HOLDOUT.value(0.74), "h90": HOLDOUT.value(0.9),
            "p_star": p_star, "p_star_two_thirds_band": 2 / 3 - p_star, "greek_face_haircut": 1 - 100 / 206}


def capital(loss: float = 20.0) -> dict[str, dict[str, float]]:
    eu = absorb(STACK, loss)
    at1_first = absorb([STACK[1], STACK[0], *STACK[2:]], STACK[1][1])   # AT1 written off in full first
    return {"eu": eu, "at1_first": at1_first}
