"""Book 18, chapter 7: valuing and negotiating an offer (undiscounted, before tax, in thousands).

The two offers of the chapter, a three-year horizon, and a candidate who either stays three years or
leaves at the end of year 1 for a job paying `next_pay` a year. Deferred bonus unvested on leaving is
forfeited; the sign-on payment is repaid in full on leaving within 24 months; a non-compete keeps the
leaver unpaid for its length.
"""
from dataclasses import dataclass
from fractions import Fraction


@dataclass(frozen=True)
class Offer:
    base: int
    first_bonus: int  # guaranteed or expected bonus for year 1
    later_bonus: int  # expected bonus for years 2 and 3
    sign_on: int
    deferred_share: Fraction  # share of each bonus deferred, vesting evenly over the next three years
    noncompete_months: int


A = Offer(base=230, first_bonus=120, later_bonus=90, sign_on=80, deferred_share=Fraction(0), noncompete_months=12)
B = Offer(base=170, first_bonus=150, later_bonus=150, sign_on=0, deferred_share=Fraction(2, 5), noncompete_months=0)


def value_if_stay(o: Offer) -> Fraction:
    """Everything earned over three years, deferrals included (they vest if the candidate stays)."""
    return o.sign_on + 3 * o.base + o.first_bonus + 2 * o.later_bonus


def value_if_leave(o: Offer, next_pay: int = 320) -> Fraction:
    """Leave at the end of year 1: keep year 1's cash, forfeit its deferral, repay the sign-on, sit out the
    non-compete, then earn next_pay a year for the rest of the three years."""
    year1_cash = o.base + o.first_bonus * (1 - o.deferred_share)
    idle = Fraction(o.noncompete_months, 12)
    later = (2 - idle) * next_pay
    repaid = o.sign_on  # repaid in full on leaving within 24 months
    return o.sign_on - repaid + year1_cash + later


def expected_value(o: Offer, p_leave, next_pay: int = 320) -> Fraction:
    p = Fraction(p_leave)
    return (1 - p) * value_if_stay(o) + p * value_if_leave(o, next_pay)


def breakeven_leave_probability(a: Offer, b: Offer, next_pay: int = 320) -> Fraction:
    """p at which the two offers are worth the same (linear in p)."""
    da = value_if_stay(a) - value_if_leave(a, next_pay)
    db = value_if_stay(b) - value_if_leave(b, next_pay)
    return (value_if_stay(a) - value_if_stay(b)) / (da - db)


def sign_on_repayment(amount, months_served: int, months_clawback: int = 24) -> Fraction:
    """Pro-rata repayment of a sign-on bonus on leaving before months_clawback months."""
    left = max(months_clawback - months_served, 0)
    return Fraction(amount) * left / months_clawback


def deferral_schedule(bonus, share, years: int = 3):
    """Cash at the bonus date and the equal annual instalments of the deferred part."""
    deferred = Fraction(bonus) * Fraction(share)
    return Fraction(bonus) - deferred, [deferred / years] * years


def forfeited(bonus, share, months_after_bonus: int, years: int = 3) -> Fraction:
    """Deferred instalments not yet paid when leaving months_after_bonus months after the bonus date
    (instalments paid at 12, 24, 36 months)."""
    _, inst = deferral_schedule(bonus, share, years)
    paid = min(months_after_bonus // 12, years)
    return sum(inst[paid:], Fraction(0))


def best_single_ask(batna, lo, hi):
    """Take-it-or-leave-it ask when the firm's walk-away value is uniform on [lo, hi] and a refusal
    leaves the candidate with batna: maximise batna + (a - batna) * P(R >= a)."""
    best = max(
        ((Fraction(a), batna + (Fraction(a) - batna) * Fraction(hi - a, hi - lo)) for a in range(lo, hi + 1)),
        key=lambda t: t[1],
    )
    a = (Fraction(batna) + hi) / 2
    return a, batna + (a - batna) * (hi - a) / (hi - lo), best
