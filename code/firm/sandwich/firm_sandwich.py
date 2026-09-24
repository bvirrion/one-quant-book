"""Sandwich and back-run simulator on a constant-product pool (build of Book 3, Chapter 22); swaps from
firm.amm, in integer base units.

A victim swaps dx_v of token A for token B with a minimum output set from the quote at submission and a
slippage tolerance. An attacker who sees it buys B with dx_a first (front-run), lets the victim trade at
the worse price, and sells the B back (back-run). The largest front-run is the one that leaves the victim
exactly at its minimum; the attacker's net profit is its gross gain less gas and the payment to the builder.
"""
import pathlib
import sys
from dataclasses import dataclass

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "amm"))
from firm_amm import cp_amount_out  # noqa: E402


@dataclass(frozen=True)
class Sandwich:
    front_in: int          # token A spent by the attacker
    victim_out: int        # token B the victim receives
    victim_loss: int       # token B it would have received without the attack, less what it got
    gross: int             # attacker's gain in token A before costs
    net: int               # after gas and builder payment


def run(ra: int, rb: int, dx_v: int, dx_a: int, fee_bps: int = 30) -> tuple[int, int]:
    """Victim output and attacker gross gain (token A) for a front-run of dx_a."""
    b_a = cp_amount_out(dx_a, ra, rb, fee_bps)
    ra1, rb1 = ra + dx_a, rb - b_a
    b_v = cp_amount_out(dx_v, ra1, rb1, fee_bps)
    ra2, rb2 = ra1 + dx_v, rb1 - b_v
    a_back = cp_amount_out(b_a, rb2, ra2, fee_bps)
    return b_v, a_back - dx_a


def min_out(ra: int, rb: int, dx_v: int, tolerance_bps: int, fee_bps: int = 30) -> int:
    return cp_amount_out(dx_v, ra, rb, fee_bps) * (10_000 - tolerance_bps) // 10_000


def max_front_run(ra: int, rb: int, dx_v: int, tolerance_bps: int, fee_bps: int = 30) -> int:
    """Largest dx_a that still lets the victim's swap execute (binary search: the victim's output falls
    as the front-run grows)."""
    floor = min_out(ra, rb, dx_v, tolerance_bps, fee_bps)
    lo, hi = 0, ra * 10
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if run(ra, rb, dx_v, mid, fee_bps)[0] >= floor:
            lo = mid
        else:
            hi = mid - 1
    return lo


def sandwich(ra: int, rb: int, dx_v: int, tolerance_bps: int, gas_cost: int, builder_share_bps: int,
             fee_bps: int = 30) -> Sandwich:
    """The attack at the largest feasible front-run; the builder is paid a share of the gross gain."""
    dx_a = max_front_run(ra, rb, dx_v, tolerance_bps, fee_bps)
    b_v, gross = run(ra, rb, dx_v, dx_a, fee_bps)
    clean = cp_amount_out(dx_v, ra, rb, fee_bps)
    tip = max(gross, 0) * builder_share_bps // 10_000
    return Sandwich(dx_a, b_v, clean - b_v, gross, gross - gas_cost - tip)


def find_sandwiches(txs: list[tuple[str, str, str]]) -> list[tuple[int, int, int]]:
    """Positions (i, j, k) of sandwich patterns in a block's list of (sender, pool, direction) swaps: the
    same sender trades one way at i and the other way at k in the same pool, around a different sender's
    trade in that pool and direction at j."""
    found = []
    for i, (s, p, d) in enumerate(txs):
        for k in range(i + 2, len(txs)):
            s2, p2, d2 = txs[k]
            if s2 == s and p2 == p and d2 != d:
                for j in range(i + 1, k):
                    if txs[j][0] != s and txs[j][1] == p and txs[j][2] == d:
                        found.append((i, j, k))
                break
    return found
