"""Chapter 8 of Book 3: metals. The LME prompt calendar, and the nickel prices of 4-8 March 2022 as
stated in the Court of Appeal's judgment ([2024] EWCA Civ 1168), with the variation margin they
imply on an illustrative short position."""
import datetime as dt
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/prompts"))
from firm_prompts import prompt_dates, variation_margin

# (label, hours after 00:00 London on Friday 4 March 2022, three-month nickel USD/t), from the judgment;
# opening at 01:00 and closing at 19:00 are this chapter's approximations of the session times, and
# 60,000 and 80,000 are the judgment's "about" and "consistently above" levels
NICKEL = [("4 Mar open", 1.0, 27_080), ("4 Mar close", 19.0, 28_919), ("7 Mar open", 73.0, 30_000),
          ("7 Mar close", 91.0, 48_078), ("8 Mar 04:49, bands suspended", 100.82, 60_000),
          ("8 Mar 06:08, peak", 102.13, 101_365), ("8 Mar 07:00", 103.0, 80_000),
          ("8 Mar 08:15, suspended", 104.25, 80_000)]
MARGIN_CALLS_BN = {"4 Mar": 2.6, "7 Mar": 7.05, "8 Mar if trades stood": 19.75}


def nickel_moves() -> dict[str, float]:
    p = {k: v for k, _, v in NICKEL}
    return {"fri": p["4 Mar close"] / p["4 Mar open"] - 1, "mon": p["7 Mar close"] / p["4 Mar close"] - 1,
            "tue": p["8 Mar 06:08, peak"] / p["7 Mar close"] - 1,
            "total": p["8 Mar 06:08, peak"] / p["4 Mar open"] - 1}


def short_squeeze(tonnes: float = 10_000) -> dict[str, float]:
    """Variation margin on a short of `tonnes` from Friday's close to Monday's close, and from
    Monday's close to Tuesday's peak (the part the cancellation removed)."""
    p = {k: v for k, _, v in NICKEL}
    mon = variation_margin(-tonnes, p["4 Mar close"], p["7 Mar close"])
    tue = variation_margin(-tonnes, p["7 Mar close"], p["8 Mar 06:08, peak"])
    return {"monday": mon, "tuesday_peak": tue, "total": mon + tue}


def calendar(trade: dt.date = dt.date(2026, 9, 24)) -> dict[str, int]:
    p = prompt_dates(trade)
    return {k: len(v) for k, v in p.items()} | {"total": len(set(p["daily"] + p["weekly"] + p["monthly"]))}
