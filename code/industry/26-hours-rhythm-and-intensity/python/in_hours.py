"""One Quant Book 17, chapter 26: hours, rhythm and intensity -- a desk's coverage requirement.

Sessions: data/industry/sessions_desk.csv (exchange sources in the ledger; CME's 24/7 crypto futures with the two weekly
maintenance windows). The week: 21-27 September 2026 (summer time in London, Frankfurt and the US). Staffing: nine-hour
shifts overlapping by one hour, two people a shift (ILLUSTRATIVE), an average week of 48 hours (EU Directive
2003/88/EC art. 6) and four weeks of leave (art. 7); on-call rota of eight engineers (ILLUSTRATIVE).
"""
import datetime as dt
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/workload"))
import firm_workload as fw  # noqa: E402

DATA = ROOT / "data/industry"
MONDAY = dt.date(2026, 9, 21)
FUTURES = ("ZN", "BRN", "FESX", "HSI")
CRYPTO = ("BTC",)
LENGTH, OVERLAP, PER_SHIFT, ROTA = 9.0, 1.0, 2, 8
NIGHTS_PER_MONTH = 365.25 / 12
INPUTS = (
    fw.Input("session hours", 0, "h", "documented", "exchange pages (ledger F1-F3)"),
    fw.Input("working-time limit", 48, "h a week", "documented", "Directive 2003/88/EC art. 6; WTR 1998 reg. 4"),
    fw.Input("annual leave", 4, "weeks", "documented", "Directive 2003/88/EC art. 7 (minimum)"),
    fw.Input("shift length", LENGTH, "h", "illustrative"),
    fw.Input("overlap", OVERLAP, "h", "illustrative"),
    fw.Input("people a shift", PER_SHIFT, "people", "illustrative"),
    fw.Input("on-call rota", ROTA, "people", "illustrative"),
    fw.Input("junior banker cap", 80, "h a week", "press", "Fortune, 12 September 2024, confirmed by the bank"),
)


def sessions():
    return fw.cal.load(str(DATA / "sessions_desk.csv"))


def matrix(roots):
    return fw.week_matrix(sessions(), list(roots), MONDAY)


def coverage():
    f, b = matrix(FUTURES), matrix(FUTURES + CRYPTO)
    return {"futures_open_h": fw.open_hours(f), "futures_closed": fw.closed_spans(f),
            "all_open_h": fw.open_hours(b), "all_closed": fw.closed_spans(b),
            "per_root_h": {r: float(b[i].sum()) / 60 for i, r in enumerate(FUTURES + CRYPTO)}}


def shifts_futures():
    tab = fw.shift_table(fw.to_markets(sessions(), list(FUTURES), MONDAY), LENGTH, OVERLAP)
    hours = sum(LENGTH for v in tab.values() for _ in v)
    return tab, hours


def staffing():
    _, fut_h = shifts_futures()
    cont_h = fw.continuous_shifts(LENGTH, OVERLAP) * LENGTH * 7
    return {"futures_shift_hours": fut_h, "futures_people": fw.headcount(fut_h, PER_SHIFT),
            "continuous_shift_hours": cont_h, "continuous_people": fw.headcount(cont_h, PER_SHIFT),
            "continuous_people_no_leave": fw.headcount(cont_h, PER_SHIFT, leave_weeks=0.0),
            "oncall": fw.oncall_nights(NIGHTS_PER_MONTH, ROTA)}


def heat():
    b = matrix(FUTURES + CRYPTO)
    n = b.sum(axis=0)
    return [[float(n[d * 1440 + h * 60:d * 1440 + (h + 1) * 60].mean()) for h in range(24)] for d in range(7)]


if __name__ == "__main__":
    c = coverage()
    print({k: v for k, v in c.items()})
    print(staffing())
    print(fw.by_status(INPUTS))
