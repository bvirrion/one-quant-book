"""firm.signoff -- the daily P&L from flash to final, its walk, the sign-off rules and their audit trail, and a
tax-drag calculator whose rates are inputs (build of One Quant Book 16, chapter 15).

Books are firm.pnl books (One Quant Book 1): prices in ledger units, exact integer cash. Start-of-day positions
enter as fills at the start-of-day marks, so a book's total at any marks is the day's P&L. The flash P&L uses the
trades captured by the flash cut-off, at the desk's flash marks, without fees. The final P&L uses every trade, fees,
and the marks after independent price verification (firm.pnlexplain.ipv, One Quant Book 6). The walk splits the
difference into market moves after the flash, late trades, fees and valuation adjustments; it adds up exactly.

API (stable):
    day_book(sod, sod_marks, fills, cut=None, fees=True) ; verified_marks(close, consensus, tolerance)
    walk(sod, sod_marks, fills, cut, flash_marks, close_marks, final_marks) -> dict
    exceptions(w, abs_tol, rel_tol, cat_tol) ; Trail (append-only audit trail) ; sign(trail, who, when, w, exc)
    tax_drag(gross, turnover, tt, div_yield, wht) ; half_turnover(net, tt) ; blended(st_rate, lt_rate, lt_share)
"""
import pathlib
import sys
from dataclasses import dataclass, field

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "pnl"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "pnlexplain"))
import firm_pnl as fp  # noqa: E402
import firm_pnlexplain as fx  # noqa: E402


def day_book(sod, sod_marks, fills, cut=None, fees=True):
    """sod: {symbol: signed quantity}; fills: [(time, symbol, side, qty, price, fee)]; cut: keep fills with
    time <= cut (None keeps all)."""
    b = fp.Book()
    for s, q in sod.items():
        if q:
            b.on_fill(s, fp.BUY if q > 0 else fp.SELL, abs(q), sod_marks[s])
    for t, s, side, q, p, fee in fills:
        if cut is None or t <= cut:
            b.on_fill(s, side, q, p, fee if fees else 0)
    return b


def verified_marks(close, consensus, tolerance):
    syms = list(close)
    v = fx.ipv([close[s] for s in syms], [consensus.get(s, close[s]) for s in syms],
               [tolerance.get(s, 0) if s in consensus else 10**12 for s in syms])
    return {s: int(round(m)) for s, (m, _) in zip(syms, v, strict=True)}


def walk(sod, sod_marks, fills, cut, flash_marks, close_marks, final_marks):
    early = day_book(sod, sod_marks, fills, cut, fees=False)
    all_nofee = day_book(sod, sod_marks, fills, None, fees=False)
    all_fee = day_book(sod, sod_marks, fills, None, fees=True)
    flash = early.total(flash_marks)
    w = {"flash": flash,
         "market moves after the flash": early.total(close_marks) - flash,
         "late trades": all_nofee.total(close_marks) - early.total(close_marks),
         "fees": all_fee.total(close_marks) - all_nofee.total(close_marks),
         "valuation adjustments": all_fee.total(final_marks) - all_fee.total(close_marks),
         "final": all_fee.total(final_marks)}
    w["unexplained"] = w["final"] - w["flash"] - sum(v for k, v in w.items() if k not in ("flash", "final"))
    return w


def exceptions(w, abs_tol, rel_tol, cat_tol):
    """Reasons to stop a sign-off: the flash-to-final difference beyond max(abs_tol, rel_tol |flash|); any
    category beyond its own tolerance; any unexplained remainder."""
    out = []
    diff = w["final"] - w["flash"]
    if abs(diff) > max(abs_tol, rel_tol * abs(w["flash"])):
        out.append(("flash to final", diff))
    for k, tol in cat_tol.items():
        if abs(w[k]) > tol:
            out.append((k, w[k]))
    if w["unexplained"] != 0:
        out.append(("unexplained", w["unexplained"]))
    return out


@dataclass
class Trail:
    entries: list = field(default_factory=list)

    def add(self, who, when, what):
        self.entries.append((len(self.entries) + 1, who, when, what))
        return self.entries[-1]


def sign(trail, who, when, w, exc):
    """Record a sign-off, or an escalation when there are exceptions; the trail is only ever appended to."""
    if exc:
        trail.add(who, when, "escalated: " + "; ".join(f"{k} {v}" for k, v in exc))
        return "escalated"
    trail.add(who, when, f"signed: final {w['final']}")
    return "signed"


def tax_drag(gross, turnover, tt, div_yield=0.0, wht=0.0):
    """Annual return after a transaction tax tt on purchases (turnover = purchases a year over capital) and a
    withholding rate wht on dividends; gross is the return before both."""
    return gross - turnover * tt - div_yield * wht


def half_turnover(net, tt):
    """The turnover at which a transaction tax takes half of a strategy's net return."""
    return net / (2 * tt)


def blended(st_rate, lt_rate, lt_share=0.6):
    """Blended rate on gains split between long- and short-term treatment (0.6 long-term: the 60/40 rule)."""
    return lt_share * lt_rate + (1 - lt_share) * st_rate
