"""One Quant Book 17, chapter 7: banks' markets divisions by product mix, from their filings and results.

data/industry/bank_markets_revenue.csv: each bank's reported fixed-income and equities markets revenue (own lines kept);
data/industry/ecb_fx_annual.csv: ECB annual average reference rates, for conversion to US dollars.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/bankmix"))
import firm_bankmix as bm  # noqa: E402

DATA = ROOT / "data/industry"


def rows():
    return bm.load(DATA / "bank_markets_revenue.csv")


def fx():
    return bm.load_fx(DATA / "ecb_fx_annual.csv")


def mix(year=2025):
    return bm.mix_table(rows(), year)


def usd(year=2025):
    f = fx()
    return {r.bank: bm.to_usd(r, f) for r in rows() if r.year == year}


def changes():
    out = {}
    banks = sorted({r.bank for r in rows()})
    for b in banks:
        ys = sorted(r.year for r in rows() if r.bank == b)
        if len(ys) > 1:
            out[b] = (ys[0], ys[-1], bm.mix_change(rows(), b, ys[0], ys[-1]))
    return out


def top3(year=2025):
    return bm.top_k_equities_share(rows(), fx(), year, 3)
