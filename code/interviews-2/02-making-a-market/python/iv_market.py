"""Exact helpers for Making a Market: break-even quotes, learning a hidden number, and a position penalty."""
from fractions import Fraction as F
from functools import cache


def posterior(prior, like_high, like_low):
    """Probability of the high value after an event with these likelihoods."""
    return prior * like_high / (prior * like_high + (1 - prior) * like_low)


def two_value_quote(low, high, prior, informed):
    """Break-even bid and ask on a two-valued contract when a share `informed` of traders know the value."""
    buy_high = informed + (1 - informed) / 2
    buy_low = (1 - informed) / 2
    ask = low + (high - low) * posterior(prior, buy_high, buy_low)
    bid = low + (high - low) * posterior(prior, buy_low, buy_high)
    return bid, ask


def hidden_number_loss(numbers):
    """Smallest expected total loss, and the best first bid, against someone who knows a number in `numbers`.

    The quote is one wide on whole numbers, and the game goes on until nothing more can be lost.
    """

    @cache
    def cost(group):
        if len(group) <= 1 or (len(group) == 2 and group[1] - group[0] <= 1):
            return F(0), None
        best = None
        for bid in range(min(group) - 1, max(group) + 1):
            low = tuple(x for x in group if x < bid)
            high = tuple(x for x in group if x > bid + 1)
            inside = tuple(x for x in group if bid <= x <= bid + 1)
            if len(inside) == len(group):
                continue  # a quote that learns nothing and loses nothing never ends the search
            total = sum(F(bid - x) for x in low) + sum(F(x - bid - 1) for x in high)
            for part in (low, high, inside):
                if part:
                    total += len(part) * cost(part)[0]
            total /= len(group)
            if best is None or total < best[0]:
                best = (total, bid)
        return best

    return cost(tuple(numbers))


def penalty_game(rounds, penalty, edge=F(1), limit=None):
    """Exact value of quoting with a penalty on the final position squared.

    Returns the value from flat, and for each number of rounds left the largest position you would buy up to.
    With `limit` the position is held inside a fixed limit, and otherwise a side comes down when that pays.
    """
    reach = 2 * rounds + 2
    value = {q: -penalty * q * q for q in range(-reach, reach + 1)}
    policy = {}
    for left in range(1, rounds + 1):
        largest = 0
        for q in range(0, reach - left + 1):
            if edge + value[q + 1] > value[q]:
                largest = q + 1
        policy[left] = largest
        new = {}
        for q in range(-reach + left, reach - left + 1):
            if limit is None:
                sell = max(edge + value[q - 1], value[q])
                buy = max(edge + value[q + 1], value[q])
            else:
                sell = edge + value[q - 1] if q - 1 >= -limit else value[q]
                buy = edge + value[q + 1] if q + 1 <= limit else value[q]
            new[q] = (sell + buy) / 2
        value = new
    return value[0], policy
