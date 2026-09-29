"""One Quant Book 16, chapter 20: seven years of an order-management system, built or bought ($ million, illustrative).

Build: seven engineers for two years, then three a year and $0.2 million of infrastructure. Buy: a $1.2 million
licence rising 5 per cent a year, a $1.0 million integration fee and two engineers in the first year, one engineer
of support after. An engineer-year costs $350,000 loaded, plus 30 per cent for what the engineer would otherwise
build. Discount rate 8 per cent. The vendor's price can jump 30 per cent at any renewal with probability 0.3;
switching vendor costs $2.0 million.
"""
import pathlib
import sys
from dataclasses import replace

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/buildbuy"))
import firm_buildbuy as bb  # noqa: E402

B = replace(bb.Build(), dev_engineers=7.0)
Y = replace(bb.Buy(), integration_fee=1.0)
R, H = 0.08, 7
U, P, X = 1.3, 0.3, 2.0


def paths(horizon=H):
    return bb.build_costs(B, horizon), bb.buy_costs(Y, horizon)


def by_horizon(max_h=12):
    return [(h, bb.npc(bb.build_costs(B, h), R), bb.npc(bb.buy_costs(Y, h), R)) for h in range(1, max_h + 1)]


def summary():
    stay, flex, opt = bb.switch_value(Y, H, R, U, P, X)
    return {"build": bb.npc(bb.build_costs(B, H), R), "buy": bb.npc(bb.buy_costs(Y, H), R),
            "breakeven_wage": bb.breakeven_wage(B, Y, H, R), "breakeven_horizon": bb.breakeven_horizon(B, Y, R),
            "buy_with_price_risk": stay, "buy_with_switch": flex, "switch_value": opt}


BASE = {"wage": 0.35, "kappa": 0.3, "dev_engineers": 7.0, "maint_engineers": 3.0, "licence": 1.2, "escalator": 0.05,
        "integration_fee": 1.0, "support_engineers": 1.0}


def diff(p):
    b = replace(B, wage=p["wage"], kappa=p["kappa"], dev_engineers=p["dev_engineers"],
                maint_engineers=p["maint_engineers"])
    y = replace(Y, wage=p["wage"], kappa=p["kappa"], licence=p["licence"], escalator=p["escalator"],
                integration_fee=p["integration_fee"], support_engineers=p["support_engineers"])
    return bb.npc(bb.build_costs(b, H), R) - bb.npc(bb.buy_costs(y, H), R)


def tornado():
    return bb.tornado(diff, BASE, 0.2)
