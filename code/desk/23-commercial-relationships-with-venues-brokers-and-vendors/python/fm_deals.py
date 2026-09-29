"""One Quant Book 16, chapter 23: a market-maker programme, a small firm and a large one (dollars a day, illustrative).

The programme's terms follow the structure of a published one (an extra rebate of $0.000075 a share for members whose
added volume exceeds 1.25 per cent of consolidated volume and who quote at the NBBO at least half the time in 2,700
symbols); consolidated volume, costs and the venue's economics are inputs. A firm quotes naturally in 2,700 symbols
per 1 per cent of consolidated volume it adds, up to 6,000.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/dealterms"))
import firm_dealterms as dt  # noqa: E402

TCV = 12e9                          # consolidated volume, shares a day (input)
PROG = dt.Programme(rebate=0.000075, volume_share=0.0125, symbols=2700)
ATTRACT, CAPTURE = 0.3, 0.0005      # taking flow attracted per share added; venue's net capture per share
DAYS = 252


def firm_at(a, pad_loss=0.001, symbol_cost=2.0):
    return dt.Firm(a, min(6000, int(round(2700 * a / 0.01))), pad_loss, symbol_cost)


SMALL, LARGE = firm_at(0.004), firm_at(0.02)
R_SMALL, R_LARGE = 0.0, 10_000.0    # outside options: none, or a rival venue's programme worth $10,000 a day


def curve():
    return [(a, dt.daily_value(PROG, firm_at(a), TCV)["net"]) for a in [x / 10000 for x in range(5, 301, 5)]]


def breakeven():
    return dt.breakeven_share(PROG, firm_at, TCV)


def tailored(firm):
    """A programme whose requirements are the firm's own natural activity."""
    return dt.Programme(PROG.rebate, firm.added_share, firm.symbols)


def deal(firm, r_f, beta=0.5, prog=None):
    prog = prog or PROG
    v = dt.daily_value(prog, firm, TCV)
    cost = v["padding"] + v["quoting"]
    gain = dt.venue_value(firm, prog, TCV, ATTRACT, CAPTURE)
    lo, hi = dt.zopa(gain, cost, r_f, 0.0)
    t = dt.nash_transfer(gain, cost, r_f, 0.0, beta)
    added = max(firm.added_share, prog.volume_share) * TCV
    return {"value": v, "cost": cost, "venue_gain": gain, "zopa": (lo, hi), "transfer": t,
            "rebate_per_share": None if t is None else t / added, "published": prog.rebate * added}
