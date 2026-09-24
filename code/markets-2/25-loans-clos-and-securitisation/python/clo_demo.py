"""Chapter 25 of Book 2: loans, CLOs and securitisation. An illustrative USD 500 million CLO (five
classes of notes and 10% equity) run through constant default rates: coverage ratios, cash diverted
from the equity, equity returns, and the default rate at which the equity stops being paid. All
parameters are illustrative; amounts in USD millions."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/waterfall"))
from firm_waterfall import Deal, Note, cutoff_cdr, equity_irr, run

CLASSES = [("AAA", 310.0, 0.013, False), ("AA", 55.0, 0.018, False), ("A", 30.0, 0.022, True),
           ("BBB", 30.0, 0.032, True), ("BB", 25.0, 0.060, True)]
PAR, EQUITY = 500.0, 50.0
OC = {1: 1.25, 2: 1.18, 3: 1.10, 4: 1.05}         # tests after AA, A, BBB and BB interest
IC = {1: 1.20}
PATH_CDRS = (0.02, 0.048, 0.07)


def deal(**kw) -> Deal:
    args = dict(notes=[Note(*c) for c in CLASSES], par=PAR, loan_spread=0.035, rate=0.04, fee=0.0045,
                oc=OC, ic=IC)
    args.update(kw)
    return Deal(**args)


def base_case() -> dict[str, float]:
    d = deal()
    periods = run(d, 0.0)
    interest = PAR * (d.rate + d.loan_spread)
    note_interest = sum(b * (d.rate + s) for _, b, s, _ in CLASSES)
    return {"interest": interest, "fee": PAR * d.fee, "note_interest": note_interest,
            "equity_year": 4 * periods[0].equity, "cash_yield": 4 * periods[0].equity / EQUITY,
            "irr": equity_irr([p.equity for p in periods], EQUITY),
            "oc": {k: PAR / sum(c[1] for c in CLASSES[:k + 1]) for k in OC},
            "cushion_bb": PAR - OC[4] * sum(c[1] for c in CLASSES)}


def irr_table(cdrs: tuple[float, ...] = tuple(k / 200 for k in range(0, 21))) -> list[tuple[float, float, float]]:
    d, out = deal(), []
    for cdr in cdrs:
        periods = run(d, cdr)
        out.append((cdr, equity_irr([p.equity for p in periods], EQUITY), sum(p.diverted for p in periods)))
    return out


def paths() -> dict[float, list[tuple[int, float, float, float]]]:
    """(quarter, par, BB-level OC ratio, equity cash) for a low, a near-cut-off and a high default rate."""
    d = deal()
    return {c: [(p.quarter, p.par, p.oc_ratios[4], p.equity) for p in run(d, c)] for c in PATH_CDRS}


def problem() -> dict[str, float]:
    d = deal()
    c = cutoff_cdr(d)
    at = run(d, c + 1e-4)
    first_cut = next(p.quarter for p in at if p.equity < 1e-9)
    high = run(d, 0.10)
    table = {round(cdr, 3): (irr, div) for cdr, irr, div in irr_table((0.0, 0.02, 0.04, 0.06, 0.08, 0.10))}
    return {"cutoff": c, "first_cut_quarter": first_cut, "par_at_cut": at[first_cut - 1].par,
            "par_loss_at_cut": PAR - at[first_cut - 1].par,
            "cum_default_at_cut": 1 - (1 - c) ** (first_cut / 4),
            "irr": {k: v[0] for k, v in table.items()}, "diverted": {k: v[1] for k, v in table.items()},
            "bb_left_10": high[-1].balances[4], "equity_final_10": high[-1].equity,
            "no_reinvest_cutoff": cutoff_cdr(deal(reinvest_quarters=8))}
