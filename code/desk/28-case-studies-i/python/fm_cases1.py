"""One Quant Book 16, chapter 28: three failures from the public record, reconstructed and rerun.

LTCM (1998): capital by period from the GAO report and the path at half the leverage. Amaranth (2006): shares of
open interest from the Senate subcommittee's record, and days to liquidate at a share of volume (volume is an input).
August 2007: Book 7's unwind simulator for a fund that sells into a crowded exit and one that holds (synthetic).
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/casebook"))
import firm_casebook as cb  # noqa: E402

AMARANTH_ADV = 25_000        # contracts a day in the month contract (illustrative input)


def ltcm():
    r = cb.ltcm_returns()
    rs = list(r.values())
    return {"returns": r, "actual": cb.capital_path(rs, cb.LTCM["nav_1997"]),
            "half": cb.capital_path(rs, cb.LTCM["nav_1997"], 0.5)}


def amaranth(share=0.2, adv=AMARANTH_ADV):
    return {"days": cb.days_to_liquidate(cb.AMARANTH["max_contracts_month"], adv, share),
            "days_10": cb.days_to_liquidate(cb.AMARANTH["max_contracts_month"], adv, 0.10)}


def august():
    return cb.quant_unwind()
