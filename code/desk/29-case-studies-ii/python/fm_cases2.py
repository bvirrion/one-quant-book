"""One Quant Book 16, chapter 29: four failures from the public record, reconstructed and rerun.

Knight (2012): the rescue's dilution from the 10-Q and the 8-K. Archegos (2021): a stylised exit race among seven
prime brokers, calibrated so that a broker with Credit Suisse's exposure and margin, selling sixth, loses Credit
Suisse's reported loss. FTX (2022): Book 3's transcription of the debtors' shortfall table and daily flows. LME nickel
(2022): a short's variation margin against its cash (the position and the cash are illustrative inputs).
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/casebook"))
import firm_casebook as cb  # noqa: E402

BROKERS = 7                   # Credit Suisse and the six other prime brokers the report names
PLACE = 6                     # the calibrated broker's place in the race (1 = first to sell)
MARGINS = (0.075, 0.094, 0.20)
SHORT_T, CASH = 10_000, 3e8   # an illustrative nickel short (tonnes) and its available cash ($)


def knight():
    k = cb.KNIGHT
    return cb.rescue(k["equity_jun_2012"], k["loss_pretax"], k["new_money"], k["new_shares"], k["shares_jun_2012"])


def race(margin=None, place=PLACE):
    a = cb.ARCHEGOS
    s = 1 / BROKERS
    impact = cb.race_impact(a["cs_loss"] / a["cs_gross_mar26"] * s, s, a["cs_margin"], (place - 1) * s)
    out = {"impact": impact}
    for m in (MARGINS if margin is None else (margin,)):
        # losses in $ billion for a broker with Credit Suisse's exposure at each place
        out[m] = [x * BROKERS * a["cs_gross_mar26"] for x in cb.exit_race([s] * BROKERS, [m] * BROKERS, impact)]
    return out


def needed_margin(impact, place, brokers=BROKERS):
    """Margin that leaves the broker at `place` whole: the average fall over its segment."""
    return impact * (place - 0.5) / brokers


def ftx():
    return {**cb.ftx_balances(), **cb.ftx_flows()}


def nickel(tonnes=SHORT_T, cash=CASH):
    n = cb.NICKEL
    return {p: cb.margin_call(tonnes, n["close_7mar"], n[p]) for p in ("price_0700_8mar", "peak_8mar")} | {
        "break": cb.break_price(tonnes, cash, n["close_7mar"])}
