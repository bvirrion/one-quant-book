"""One Quant Book 17, chapter 23: structurer, sales and sales-trader -- the margin in a note.

The note: an ILLUSTRATIVE five-year Phoenix autocallable on one index (annual observations, autocall at 100%, coupon
barrier 70% with memory, capital protected unless the index ends below 60%), priced with Book 5's firm.autocall
(flat volatility, dividend yield 2%, discounting at the risk-free rate; an issuer's own funding spread would add to
the margin). Margin = 100 minus the note's fair value per 100 sold at par. Market size: EUSIPA's Q1 2026 report
(constants below, ledger F1). Pay: the survey's securities sales agents (oews_roles.csv).
"""
import csv
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/roles"))
import firm_roles as fr  # noqa: E402

DATA = ROOT / "data/industry"
OBS = (1.0, 2.0, 3.0, 4.0, 5.0)
Q = 0.02
RATES = (0.01, 0.04)
VOLS = (0.20, 0.30)
COUPON = 6.0                   # per year, per 100, for the fixed-coupon table
TARGET = 2.0                   # margin per 100 for the fair-coupon table
N, SEED, STEPS = 200_000, 23, 12
# EUSIPA Market Report Q1 2026 (ledger F1): outstanding volume of investment products by market, EUR million
EUSIPA_OUTSTANDING = {"Switzerland": 286_264, "Germany": 99_890, "Italy": 66_788, "Austria": 17_462,
                      "Belgium": 11_678, "Luxembourg": 4_553}
EUSIPA_TOTAL = 486_635
EUSIPA_TURNOVER_Q1 = 19_000    # investment products traded on venues, Q1 2026, EUR million ('EUR 19 billion')
DESK_ISSUANCE = (1e9, 5e9)     # a desk's annual issuance, EUR (illustrative)
STRUCTURERS = 10               # a desk's structurers (illustrative)


def fr_ac():
    sys.path.insert(0, str(ROOT / "code/firm/autocall"))
    import firm_autocall as ac

    return ac


def sheet(coupon):
    return fr_ac().TermSheet(obs_times=OBS, trigger=1.0, coupon=coupon, coupon_barrier=0.7, memory=True, protection=0.6)


def margins(n=N):
    return {(r, v): fr.structuring_margin(sheet, COUPON, TARGET, r, Q, v, n, SEED, STEPS) for r in RATES for v in VOLS}


def revenue_per_structurer(margin_pct=TARGET, issuance=DESK_ISSUANCE, people=STRUCTURERS):
    return tuple(i * margin_pct / 100.0 / people for i in issuance)


def survey(occ="41-3031"):
    with open(DATA / "oews_roles.csv") as f:
        return {r["naics"]: r for r in csv.DictReader(f) if r["occ"] == occ}


def eusipa_shares():
    return {k: v / EUSIPA_TOTAL for k, v in EUSIPA_OUTSTANDING.items()}


if __name__ == "__main__":
    for k, v in margins().items():
        print(k, {a: round(b, 3) for a, b in v.items()})
    print(revenue_per_structurer(), eusipa_shares(), sum(EUSIPA_OUTSTANDING.values()))
    s = survey()
    for k in ("523000", "5220A1", "52"):
        print(k, s[k]["employment"], s[k]["p10"], s[k]["p50"], s[k]["p90"])
