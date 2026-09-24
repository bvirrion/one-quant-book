"""Chapter 10 of Book 2: swap clearing and the clearing-house basis. Initial-margin profiles over a
swap's life, the margin valuation adjustment, and the basis a dealer charges for carrying one-way
positions at two clearing houses. Model parameters are illustrative."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/ccpbasis"))
from firm_ccpbasis import MarginModel, annuity_remaining, basis_bp, im_path, mva

MODEL = MarginModel()               # 7 bp a day, 5-day margin period, 99%
RATE = 0.04
FUNDING = 0.005                     # funding spread on posted margin, 50 bp a year


def im_profiles() -> list[tuple[float, float, float]]:
    """(years elapsed, IM of a 10-year swap, IM of a 30-year swap), USD million, per 100 million."""
    ten = dict(im_path(1e8, 10, RATE, MODEL))
    thirty = dict(im_path(1e8, 30, RATE, MODEL))
    return [(t, ten.get(t, 0.0) / 1e6, v / 1e6) for t, v in thirty.items()]


def basis_table() -> list[tuple[int, float, float, float]]:
    """(maturity, basis bp per one-way position at 25, 50, 75 bp funding)."""
    return [(n, *(basis_bp(1e8, n, RATE, MODEL, f) for f in (0.0025, 0.005, 0.0075))) for n in (2, 5, 10, 20, 30)]


def one_way_book(notional: float = 2e9, maturity: int = 10) -> dict[str, float]:
    dv01 = notional * annuity_remaining(0.0, maturity, RATE) * 1e-4
    im = dv01 * MODEL.im_per_dv01()
    m = mva(notional, maturity, RATE, MODEL, FUNDING)
    return {"dv01": dv01, "im": im, "vm_5bp": 5 * dv01, "mva": m, "mva_two": 2 * m,
            "basis_one": basis_bp(notional, maturity, RATE, MODEL, FUNDING),
            "basis_two": basis_bp(notional, maturity, RATE, MODEL, FUNDING, ccps=2),
            "basis_two_30y": basis_bp(notional, 30, RATE, MODEL, FUNDING, ccps=2),
            "im_10day": dv01 * MarginModel(mpor_days=10).im_per_dv01()}
