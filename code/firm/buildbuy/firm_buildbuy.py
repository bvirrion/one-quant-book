"""firm.buildbuy -- build against buy for a trading system: cost paths, net present cost, the break-even engineer
cost, the option to switch vendors on a binomial tree, and a tornado of the inputs (build of One Quant Book 16,
chapter 20).

Build: `dev_years` years of `dev_engineers`, then `maint_engineers` a year, plus infrastructure; an engineer-year costs
the loaded wage w plus an opportunity cost kappa w (what the engineer would have produced elsewhere). Buy: a licence
growing at an escalator, integration in the first year (a fee plus engineers), and support engineers every year.
Switching: at each year end the vendor's price multiplier moves up by u with probability p or stays (d = 1); the firm
may switch to another vendor at cost X, which resets the multiplier to one. The option's value is the expected cost
of staying minus the expected cost with the best switching policy (backward induction on the tree).

API (stable):
    Build(...) ; Buy(...) ; build_costs(b, horizon) ; buy_costs(y, horizon) ; npc(costs, r)
    breakeven_wage(b, y, horizon, r) ; breakeven_horizon(b, y, r) ; switch_value(y, horizon, r, u, p, switch_cost)
    switch_policy(y, horizon, r, u, p, switch_cost) ; tornado(f, base, bump)
"""
from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Build:
    wage: float = 0.35                  # loaded cost of an engineer-year ($ million)
    kappa: float = 0.3                  # opportunity cost as a share of the wage
    dev_engineers: float = 6.0
    dev_years: int = 2
    maint_engineers: float = 3.0
    infra: float = 0.2                  # a year


@dataclass(frozen=True)
class Buy:
    licence: float = 1.2                # first-year licence ($ million)
    escalator: float = 0.05
    integration_fee: float = 1.5
    integration_engineers: float = 2.0  # in the first year
    support_engineers: float = 1.0
    wage: float = 0.35
    kappa: float = 0.3


def build_costs(b, horizon):
    ey = b.wage * (1 + b.kappa)
    return [b.dev_engineers * ey if t < b.dev_years else b.maint_engineers * ey + b.infra for t in range(horizon)]


def buy_costs(y, horizon):
    ey = y.wage * (1 + y.kappa)
    out = []
    for t in range(horizon):
        c = y.licence * (1 + y.escalator) ** t + y.support_engineers * ey
        if t == 0:
            c += y.integration_fee + y.integration_engineers * ey
        out.append(c)
    return out


def npc(costs, r):
    """Net present cost, each year's cost paid at the year end."""
    return sum(c / (1 + r) ** (t + 1) for t, c in enumerate(costs))


def breakeven_wage(b, y, horizon, r):
    """The loaded engineer-year cost at which building and buying cost the same (both are linear in the wage)."""
    def diff(w):
        return npc(build_costs(replace(b, wage=w), horizon), r) - npc(buy_costs(replace(y, wage=w), horizon), r)
    d0, d1 = diff(0.0), diff(1.0)
    return -d0 / (d1 - d0)


def breakeven_horizon(b, y, r, max_h=30):
    """The horizon (years) from which building costs no more than buying at every longer horizon up to max_h; None if
    buying is cheaper at max_h."""
    worse = [h for h in range(1, max_h + 1) if npc(build_costs(b, h), r) > npc(buy_costs(y, h), r)]
    if worse and worse[-1] == max_h:
        return None
    return worse[-1] + 1 if worse else 1


def _tree(y, horizon, r, u, p, switch_cost, allow):
    base = buy_costs(y, horizon)
    lic = [y.licence * (1 + y.escalator) ** t for t in range(horizon)]
    disc = [1 / (1 + r) ** (t + 1) for t in range(horizon)]
    memo, policy = {}, set()

    def v(t, k):                        # k: number of price rises in the current multiplier
        if t == horizon:
            return 0.0
        if (t, k) in memo:
            return memo[(t, k)]
        stay = (base[t] + lic[t] * (u ** k - 1)) * disc[t] + p * v(t + 1, k + 1) + (1 - p) * v(t + 1, k)
        best = stay
        if allow and k > 0:
            sw = (switch_cost + base[t]) * disc[t] + p * v(t + 1, 1) + (1 - p) * v(t + 1, 0)
            if sw < stay:
                best = sw
                policy.add((t + 1, k))
        memo[(t, k)] = best
        return best
    return v(0, 0), policy


def switch_value(y, horizon, r, u, p, switch_cost):
    """(expected NPC of staying, expected NPC with the best switching policy, option value) on the price tree."""
    stay, _ = _tree(y, horizon, r, u, p, switch_cost, False)
    flex, _ = _tree(y, horizon, r, u, p, switch_cost, True)
    return stay, flex, stay - flex


def switch_policy(y, horizon, r, u, p, switch_cost):
    """The (year, price rises so far) states in which switching is optimal."""
    return sorted(_tree(y, horizon, r, u, p, switch_cost, True)[1])


def tornado(f, base, bump=0.2):
    """f(params) -> value; returns [(name, low, high)] for each parameter moved by -bump and +bump, widest first."""
    rows = []
    for k, v in base.items():
        lo, hi = f({**base, k: v * (1 - bump)}), f({**base, k: v * (1 + bump)})
        rows.append((k, lo, hi))
    return sorted(rows, key=lambda x: -abs(x[2] - x[1]))
