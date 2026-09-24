"""Chapter 28 of Book 2: getting access to rates and credit. Three routes to Treasury repo and
interest-rate swaps for a fund, costed by the access-cost model: rent (sponsored repo and a swap
clearing broker), buy (direct membership), and bilateral (uncleared repo and swaps). All costs are
illustrative; the fund's swap notional is twice its repo balance."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/clearcost"))
from firm_clearcost import Route, annual_cost, breakeven, cheapest, unit_cost

FUNDING = 0.005                  # spread paid to fund posted margin, a year
MIX = 2.0                        # swap notional per unit of repo balance
RENT = Route("rent", fixed=0.5e6, repo_bp=8.0, swap_bp=0.5, repo_margin=0.02, swap_margin=0.015)
BUY = Route("buy", fixed=8e6, repo_bp=1.0, swap_bp=0.2, repo_margin=0.02, swap_margin=0.015, fund_share=0.002)
BILATERAL = Route("bilateral", fixed=0.2e6, repo_bp=12.0, swap_bp=1.0, repo_margin=0.03, swap_margin=0.03)
ROUTES = [RENT, BUY, BILATERAL]


def cost_curves(max_bn: int = 30, step: float = 0.5) -> list[tuple[float, ...]]:
    """(repo balance in USD bn, annual cost of each route in USD m)."""
    out = []
    for k in range(int(max_bn / step) + 1):
        b = k * step * 1e9
        out.append((k * step, *(annual_cost(r, b, MIX * b, FUNDING) / 1e6 for r in ROUTES)))
    return out


def sensitivity(spreads: tuple[float, ...] = tuple(4 + 0.5 * k for k in range(17))) -> list[tuple[float, float]]:
    """(sponsor spread bp, break-even repo balance in USD bn between renting and buying)."""
    out = []
    for s in spreads:
        rent = Route("rent", RENT.fixed, s, RENT.swap_bp, RENT.repo_margin, RENT.swap_margin)
        b = breakeven(rent, BUY, MIX, FUNDING)
        out.append((s, b / 1e9 if b else float("nan")))
    return out


def tutorial() -> dict[str, float]:
    units = {r.name: 1e4 * unit_cost(r, MIX, FUNDING) for r in ROUTES}
    mid = {r.name: annual_cost(r, 5e9, 10e9, FUNDING) / 1e6 for r in ROUTES}
    return {"unit_rent": units["rent"], "unit_buy": units["buy"], "unit_bilateral": units["bilateral"],
            "mid_rent": mid["rent"], "mid_buy": mid["buy"], "mid_bilateral": mid["bilateral"],
            "mid_best": cheapest(ROUTES, 5e9, 10e9, FUNDING).name,
            "be_rent_buy": breakeven(RENT, BUY, MIX, FUNDING) / 1e9,
            "be_bilateral_rent": breakeven(BILATERAL, RENT, MIX, FUNDING) / 1e9}


def problem() -> dict[str, float]:
    t = tutorial()
    b = t["be_rent_buy"] * 1e9
    no_swaps = breakeven(RENT, BUY, 0.0, FUNDING) / 1e9
    dearer = Route("buy", 12e6, BUY.repo_bp, BUY.swap_bp, BUY.repo_margin, BUY.swap_margin, BUY.fund_share)
    return {**t, "cost_at_be": annual_cost(RENT, b, MIX * b, FUNDING) / 1e6,
            "be_no_swaps": no_swaps, "be_fixed_12": breakeven(RENT, dearer, MIX, FUNDING) / 1e9,
            "be_spread_5": dict(sensitivity((5.0,)))[5.0], "be_spread_12": dict(sensitivity((12.0,)))[12.0],
            "saving_20": (annual_cost(RENT, 20e9, 40e9, FUNDING) - annual_cost(BUY, 20e9, 40e9, FUNDING)) / 1e6}
