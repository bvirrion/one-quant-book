"""A victim's swap with a limit on its price, and a trader who moves first and last."""


def out(a, r_in, r_out, keep=0.997):
    return a * keep * r_out / (r_in + a * keep)


def victim_gets(front, victim_in, x, y):
    bought = out(front, x, y)
    return out(victim_in, x + front, y - bought)


def profit(front, victim_in, x, y):
    bought = out(front, x, y)
    x1, y1 = x + front, y - bought
    got = out(victim_in, x1, y1)
    return out(bought, y1 - got, x1 + victim_in) - front


def largest_front(victim_in, x, y, slippage):
    """The most the front-runner can trade with the victim still inside its limit."""
    floor = out(victim_in, x, y) * (1 - slippage)
    if victim_gets(0.0, victim_in, x, y) < floor:
        return 0.0
    low, high = 0.0, 100.0 * x
    for _ in range(200):
        mid = (low + high) / 2
        low, high = (mid, high) if victim_gets(mid, victim_in, x, y) >= floor else (low, mid)
    return low
