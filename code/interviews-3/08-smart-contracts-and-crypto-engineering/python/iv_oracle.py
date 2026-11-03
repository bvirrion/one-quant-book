"""A loan valued at a pool's spot price, with the price pushed up for one transaction."""
from iv_amm import Pool

UNIT = 10**18           # a pool counts in 18 decimals, not in whole tokens


def attack(x, y, flash, own, ltv, fee_bps=30, fair_oracle=None):
    """Own `own` tokens, flash-borrow `flash` dollars. Returns profit at the true price."""
    fair = y / x
    pool = Pool(x * UNIT, y * UNIT, fee_bps)
    tokens = pool.buy_x(int(flash * UNIT))
    oracle = fair_oracle if fair_oracle is not None else pool.price()
    borrowed = own * oracle * ltv            # the collateral stays with the lender
    back = pool.buy_y(tokens) / UNIT
    return borrowed + back - flash - own * fair
