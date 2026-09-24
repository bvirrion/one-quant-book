"""Chapter 11 of Book 2: inflation markets. A ten-year TIPS through 2022, the ten-year nominal, real
and breakeven yields, CPI seasonality, the monthly accrual of the TIPS reference index, and the
carry of a repo-financed TIPS in August 2022. Bond terms and the repo rate are illustrative; index
and yield data are from FRED (data/markets-2)."""
import csv
import datetime as dt
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/breakeven"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/bond"))
from firm_bond import Bond
from firm_breakeven import Index, breakeven, index_ratio, linker_carry, monthly_accrual, ref_index, seasonal_factors

DATA = pathlib.Path(__file__).resolve().parents[4] / "data/markets-2"
TIPS = Bond(0.125, dt.date(2032, 1, 15))     # a ten-year TIPS dated 15 January 2022 (illustrative)
DATED = dt.date(2022, 1, 15)


def load_cpi(column: str = "nsa") -> Index:
    with open(DATA / "cpi_us_monthly.csv") as f:
        return {(int(r["date"][:4]), int(r["date"][5:7])): float(r[column]) for r in csv.DictReader(f)}


def load_tips10() -> list[tuple[str, float, float, float]]:
    with open(DATA / "tips10_monthend.csv") as f:
        return [(r["date"], float(r["nominal"]), float(r["real"]), float(r["breakeven"])) for r in csv.DictReader(f)]


def hook_2022() -> dict[str, float]:
    """Bought 3 Jan 2022 at a real yield of -0.97%, marked 30 Dec 2022 at 1.58% (the FRED 10-year
    real yields on those days); per 100 face, dirty real prices times index ratios, plus July's coupon."""
    cpi = load_cpi()
    d0, d1 = dt.date(2022, 1, 3), dt.date(2022, 12, 30)
    p0, p1 = TIPS.dirty_price(-0.0097, d0), TIPS.dirty_price(0.0158, d1)
    i0, i1 = ref_index(d0, cpi) / ref_index(DATED, cpi), ref_index(d1, cpi) / ref_index(DATED, cpi)
    coupon = TIPS.coupon / 2 * index_ratio(dt.date(2022, 7, 15), DATED, cpi)
    return {"p0": p0, "p1": p1, "i0": i0, "i1": i1, "coupon": coupon,
            "price_only": p1 / p0 - 1, "index_only": i1 / i0 - 1,
            "total": (p1 * i1 + coupon) / (p0 * i0) - 1,
            "cpi_dec": cpi[(2022, 12)] / cpi[(2021, 12)] - 1, "cpi_jun": cpi[(2022, 6)] / cpi[(2021, 6)] - 1}


def seasonality(first: int = 2010, last: int = 2024) -> dict[int, float]:
    cpi = {k: v for k, v in load_cpi().items() if first - 1 <= k[0] <= last}
    return seasonal_factors(cpi)


def accruals(first: tuple[int, int] = (2021, 1), last: tuple[int, int] = (2023, 12)) -> list[tuple[str, float]]:
    """(YYYY-MM, % growth of the TIPS reference index over that calendar month)."""
    cpi, out = load_cpi(), []
    y, m = first
    while (y, m) <= last:
        out.append((f"{y}-{m:02d}", 100 * monthly_accrual(y, m, cpi)))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


# ---- the weekend problem: carry of a repo-financed TIPS in August 2022 -----------------------------
FACE = 100_000_000.0
REAL = 0.0014            # FRED 10-year real yield, 29 July 2022
NOMINAL = 0.0267         # FRED 10-year nominal yield, 29 July 2022
REPO = 0.0230            # illustrative, about SOFR in early August 2022
DAYS = 31


def august_2022() -> dict[str, float]:
    cpi = load_cpi()
    aug1, sep1 = dt.date(2022, 8, 1), dt.date(2022, 9, 1)
    ir = index_ratio(aug1, DATED, cpi)
    mv = FACE / 100 * TIPS.dirty_price(REAL, aug1) * ir
    acc = monthly_accrual(2022, 8, cpi)
    carry = linker_carry(mv, acc, REAL, REPO, DAYS)
    return {"ref_dated": ref_index(DATED, cpi), "ref_aug1": ref_index(aug1, cpi), "ref_sep1": ref_index(sep1, cpi),
            "ref_aug15": ref_index(dt.date(2022, 8, 15), cpi), "ir": ir, "price": TIPS.dirty_price(REAL, aug1),
            "mv": mv, "accrual": acc, "accrual_income": mv * acc,
            "real_pull": mv * ((1 + REAL) ** (DAYS / 365) - 1), "repo_cost": mv * REPO * DAYS / 360,
            "carry": carry, "nominal_carry": linker_carry(mv, 0.0, NOMINAL, REPO, DAYS),
            "accrual_annualised": (1 + acc) ** 12 - 1, "sep_accrual": monthly_accrual(2022, 9, cpi),
            "sep_carry": linker_carry(mv, monthly_accrual(2022, 9, cpi), REAL, REPO, 30),
            "dv01": FACE / 100 * TIPS.risk(REAL, aug1)["dv01"] * ir}


def fisher_vs_difference(nominal: float = 0.0267, real: float = 0.0014) -> tuple[float, float]:
    return breakeven(nominal, real), nominal - real
