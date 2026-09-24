"""AMM library in integer fixed point (build of Book 3, Chapter 20); the Rust crate firm_amm is the twin
of the constant-product and stableswap parts.

Constant product: Uniswap v2's integer swap with the fee taken on the input. Concentrated liquidity:
Uniswap v3's ticks (price = 1.0001^tick), square-root prices in Q64.96 and the token amounts of a
position over a range. Stableswap: Curve's invariant A n^n S + D = A D n^n + D^(n+1) / (n^n prod x),
solved for D and for one balance by the integer Newton iterations of the reference implementation.
"""
import math

Q96 = 1 << 96


def cp_amount_out(amount_in: int, reserve_in: int, reserve_out: int, fee_bps: int = 30) -> int:
    """Output of a constant-product swap; the fee stays in the pool (floor division, as on chain)."""
    a = amount_in * (10_000 - fee_bps)
    return a * reserve_out // (reserve_in * 10_000 + a)


def cp_amount_in(amount_out: int, reserve_in: int, reserve_out: int, fee_bps: int = 30) -> int:
    """Input needed for an exact output (rounded up by one unit, as on chain)."""
    return reserve_in * amount_out * 10_000 // ((reserve_out - amount_out) * (10_000 - fee_bps)) + 1


def tick_at_price(price: float) -> int:
    return math.floor(math.log(price) / math.log(1.0001))


def sqrt_price_x96(tick: int) -> int:
    """sqrt(1.0001^tick) in Q64.96, to double precision (the chain's TickMath is exact to the last bit)."""
    return int(math.isqrt(int(1.0001 ** tick * (1 << 192))))


def amounts_for_liquidity(liq: int, sp: int, sa: int, sb: int) -> tuple[int, int]:
    """Token0 and token1 held by liquidity `liq` over [sa, sb) at square-root price sp (all Q64.96):
    amount0 = L (sb - s)/(s sb), amount1 = L (s - sa), with s clipped to the range; rounded down."""
    s = min(max(sp, sa), sb)
    a0 = liq * (sb - s) * Q96 // (s * sb)
    a1 = liq * (s - sa) // Q96
    return a0, a1


def next_sqrt_price_from_amount0(sp: int, liq: int, amount0_in: int) -> int:
    """Price after adding token0 within one range: L s / (L + dx s), rounded up."""
    num = liq * Q96 * sp
    den = liq * Q96 + amount0_in * sp
    return -(-num // den)


def ss_get_d(xp: list[int], amp: int) -> int:
    """Stableswap invariant D for balances xp and amplification A (Newton, integer)."""
    n, s = len(xp), sum(xp)
    if s == 0:
        return 0
    d, ann = s, amp * n
    for _ in range(255):
        d_p = d
        for x in xp:
            d_p = d_p * d // (x * n)
        d_prev = d
        d = (ann * s + d_p * n) * d // ((ann - 1) * d + (n + 1) * d_p)
        if abs(d - d_prev) <= 1:
            return d
    raise ArithmeticError("D did not converge")


def ss_get_y(i: int, j: int, x: int, xp: list[int], amp: int) -> int:
    """New balance of coin j when coin i's balance is set to x, keeping D (Newton, integer)."""
    n = len(xp)
    d = ss_get_d(xp, amp)
    ann, c, s_ = amp * n, d, 0
    for k in range(n):
        if k == j:
            continue
        xk = x if k == i else xp[k]
        s_ += xk
        c = c * d // (xk * n)
    c = c * d // (ann * n)
    b = s_ + d // ann
    y = d
    for _ in range(255):
        y_prev = y
        y = (y * y + c) // (2 * y + b - d)
        if abs(y - y_prev) <= 1:
            return y
    raise ArithmeticError("y did not converge")


def ss_amount_out(i: int, j: int, dx: int, xp: list[int], amp: int, fee_bps: int = 4) -> int:
    """Stableswap output of coin j for dx of coin i, fee taken on the output."""
    dy = xp[j] - ss_get_y(i, j, xp[i] + dx, xp, amp) - 1
    return dy - dy * fee_bps // 10_000
