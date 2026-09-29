"""One Quant Book 17, chapter 11: reading a trading firm's accounts.

data/industry/filings_snapshot/: facts extracted from filed accounts, one row per fact with its filing and page (or
iXBRL context, or EDGAR accession). Quadrature Capital Limited's six fiscal years (February to January) come from one
inline-XBRL filing (quadrature_ixbrl.csv, written by in_fetch.py) and two image-only filings transcribed by hand
(quadrature_pdf.csv); Jane Street's two UK entities and Squarepoint Capital LLP are transcribed from image-only
filings; Virtu Financial's lines come from SEC company facts. Everything here reads the committed snapshot.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/filings"))
sys.path.insert(0, str(ROOT / "code/firm/bankmix"))
import firm_bankmix as bm  # noqa: E402
import firm_filings as ff  # noqa: E402

SNAP = ROOT / "data/industry/filings_snapshot"
Q = "Quadrature Capital Limited"
L = "Jane Street UK Partnership LLP"
G = "Jane Street Europe Limited (group)"
P = "Squarepoint Capital LLP"
V = "Virtu Financial Inc."
VIRTU_EMPLOYEES_2025 = 1027  # chapter 1, F5: 'approximately 1,027 employees' (10-K for 2025; a count at a date)
BARCLAYS_REM4 = [312, 150, 70, 58, 45, 18, 15, 10, 15, 10, 7, 2, 2, 1, 0, 0, 0, 0, 1, 1]  # EUR 1m bands, ledger F7
BARCLAYS_IB = dict(staff=4.0 + 808.3, total=1263.3, variable=732.8, fixed=530.5)  # GBP m, UK REM5, ledger F7
OP_PARTS = [("Revenue", 1), ("AdministrativeExpenses", -1), ("OtherOperatingIncome", 1)]


def snapshot():
    return ff.Snapshot.load(*sorted(SNAP.glob("*.csv")))


def quadrature(s=None):
    """Per fiscal year (label = calendar year of the January year end): the chapter's table, amounts in GBP m."""
    s = s or snapshot()
    rows = []
    for end in s.ends(Q):
        rev, staff, n, op, pbt, pat, div = (s.get(Q, c, end) for c in (
            "Revenue", "StaffCosts", "AverageEmployees", "OperatingProfit", "ProfitBeforeTax", "ProfitAfterTax",
            "DividendsPaid"))
        rows.append(dict(fy=int(end[:4]), revenue=rev / 1e6, staff=staff / 1e6, employees=int(n),
                         staff_per_head=staff / n / 1e6, revenue_per_head=rev / n / 1e6, comp_ratio=staff / rev,
                         op_margin=op / rev, below_op=(pbt - op) / 1e6, profit_after_tax=pat / 1e6,
                         dividends=-div / 1e6))
    return rows


def quadrature_result(s=None):
    """The weekend problem's named result: ranges per head and the share of six years' profit paid out."""
    rows = quadrature(s)
    return dict(staff_per_head=(min(r["staff_per_head"] for r in rows), max(r["staff_per_head"] for r in rows)),
                revenue_per_head=(min(r["revenue_per_head"] for r in rows), max(r["revenue_per_head"] for r in rows)),
                comp_ratio=(min(r["comp_ratio"] for r in rows), max(r["comp_ratio"] for r in rows)),
                paid_out=sum(r["dividends"] for r in rows) / sum(r["profit_after_tax"] for r in rows),
                profit=sum(r["profit_after_tax"] for r in rows), dividends=sum(r["dividends"] for r in rows))


def quadrature_reconcile(s=None, fixed=False):
    """Operating profit against revenue - administrative expenses + other income; fixed=True reverses the one
    fact whose tag carries a minus sign although the statement shows it as income."""
    s = s or snapshot()
    if fixed:
        s = ff.Snapshot([ff.Fact(f.entity, f.concept, -f.value, f.unit, f.start, f.end, f.source, f.locator,
                                 f.note + "; sign reversed") if (f.entity, f.concept) == (Q, "OtherOperatingIncome")
                         else f for f in s.facts])
    return s.reconcile(Q, "OperatingProfit", OP_PARTS, tol=0.5)


def jane_street(s=None):
    """Both UK entities by calendar year: revenue and staff costs in USD m, headcount, staff cost per head in USD m."""
    s = s or snapshot()
    out = []
    for ent in (G, L):
        for end, rev in s.series(ent, "Revenue"):
            st, n = s.get(ent, "StaffCosts", end), s.get(ent, "AverageEmployees", end)
            start = [f.start for f in s.facts if f.entity == ent and f.end == end and f.concept == "Revenue"][0]
            m = ff.months(start, end)
            out.append(dict(entity=ent, year=int(end[:4]), months=m, revenue=rev / 1e6,
                            staff=None if st is None else st / 1e6, employees=n,
                            staff_per_head=None if not (st and n) else st / n / 1e6,
                            staff_per_head_annual=None if not (st and n) else st / n / 1e6 * 12 / m))
    return out


def members(s=None):
    """The LLP's profit before members' shares: per member, per employee, and the largest (corporate) member's share."""
    s = s or snapshot()
    out = []
    for end, pbm in s.series(L, "ProfitBeforeMembers"):
        nm, ne, big = (s.get(L, c, end) for c in ("AverageMembers", "AverageEmployees", "LargestMemberShare"))
        out.append(dict(year=int(end[:4]), profit=pbm / 1e6, per_member=pbm / nm / 1e6, per_employee=pbm / ne / 1e6,
                        largest_share=None if big is None else big / pbm,
                        profit_to_staff=pbm / s.get(L, "StaffCosts", end)))
    return out


def squarepoint(s=None):
    s = s or snapshot()
    return [dict(year=int(e[:4]), revenue=s.get(P, "Revenue", e) / 1e6,
                 charge_per_secondee=v / s.get(P, "AverageSecondees", e),
                 profit=s.get(P, "ProfitBeforeMembers", e) / 1e6) for e, v in s.series(P, "ServiceCharges")]


def virtu(s=None):
    s = s or snapshot()
    rows = []
    for end, rev in s.series(V, "Revenue"):
        st, tg = s.get(V, "StaffCosts", end), s.get(V, "TradingGains", end)
        rows.append(dict(year=int(end[:4]), revenue=rev / 1e6, staff=st / 1e6, trading=tg / 1e6,
                         comp_ratio=st / rev, comp_to_trading=st / tg))
    return rows


def fx_gbp_usd(year):
    return bm.load_fx(ROOT / "data/industry/ecb_fx_annual.csv")[year]["GBP"]


def barclays():
    n = sum(BARCLAYS_REM4)
    return dict(high_earners=n, under_2m=(BARCLAYS_REM4[0] + BARCLAYS_REM4[1]) / n,
                from_5m=sum(BARCLAYS_REM4[8:]), ib_mean=BARCLAYS_IB["total"] / BARCLAYS_IB["staff"],
                ib_variable_share=BARCLAYS_IB["variable"] / BARCLAYS_IB["total"])


def statements(s=None):
    """Quadrature's years as firm.firmecon Statements (all staff costs as compensation, the rest as other fixed)."""
    s = s or snapshot()
    mapping = {"net_revenue": [("Revenue", 1)], "comp": [("StaffCosts", 1)],
               "other_fixed": [("AdministrativeExpenses", 1), ("StaffCosts", -1)]}
    return [ff.to_statement(s, Q, e, mapping, headcount="AverageEmployees") for e in s.ends(Q)]


if __name__ == "__main__":
    for r in quadrature():
        print({k: round(v, 3) if isinstance(v, float) else v for k, v in r.items()})
    print(quadrature_result())
    print(quadrature_reconcile(), quadrature_reconcile(fixed=True))
    for r in jane_street():
        print(r)
    print(members())
    print(squarepoint())
    print(virtu())
    print(barclays(), fx_gbp_usd(2024))
