"""Numbers gate: every numerical answer printed in Book 17, chapter 11 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import in_accounts as a  # noqa: E402

S = a.snapshot()


def r(x, d=1):
    return round(float(x), d)


def test_snapshot_clean():
    assert S.problems() == []
    assert a.quadrature_reconcile(S) == [("2025-01-31", 556_556_000.0, 521_054_000.0)]
    assert a.quadrature_reconcile(S, fixed=True) == []
    st, comp = a.quadrature_reconcile(S)[0][1:]
    assert r((st - comp) / 1e6, 3) == 35.502 and r(comp / 1e6) == 521.1


def test_quadrature_table():
    q = {x["fy"]: x for x in a.quadrature(S)}
    ys = range(2020, 2026)
    assert [r(q[y]["revenue"]) for y in ys] == [140.6, 269.8, 778.6, 664.2, 588.2, 1224.8]
    assert [r(q[y]["staff"]) for y in ys] == [116.7, 182.9, 409.0, 394.7, 408.0, 556.1]
    assert [q[y]["employees"] for y in ys] == [68, 83, 98, 113, 143, 173]
    assert [r(q[y]["staff_per_head"], 2) for y in ys] == [1.72, 2.20, 4.17, 3.49, 2.85, 3.21]
    assert [r(q[y]["revenue_per_head"], 2) for y in ys] == [2.07, 3.25, 7.94, 5.88, 4.11, 7.08]
    assert [r(100 * q[y]["comp_ratio"]) for y in ys] == [83.0, 67.8, 52.5, 59.4, 69.4, 45.4]
    assert [r(q[y]["profit_after_tax"]) for y in ys] == [244.2, 262.7, 525.6, 225.6, 49.6, 410.7]
    assert [r(q[y]["dividends"]) for y in ys] == [4.0, 1.0, 0.0, 0.0, 1329.4, 360.0]
    assert [round(q[y]["below_op"]) for y in range(2020, 2024)] == [234, 250, 351, 179]
    fv = S.series(a.Q, "FairValueGains")
    assert [r(v / 1e6) for _, v in fv] == [233.9, 249.7, 350.7, 178.3]
    assert r(S.get(a.Q, "SocialSecurityCosts", "2025-01-31") / 1e6) == 74.4
    assert r(-S.get(a.Q, "DividendsPaid", "2024-01-31") / 1e6) == 1329.4
    assert r(S.get(a.Q, "OtherOperatingIncome", "2025-01-31") / 1e6, 3) == -17.751


def test_quadrature_result():
    res = a.quadrature_result(S)
    assert [r(x, 2) for x in res["staff_per_head"]] == [1.72, 4.17]
    assert [r(x, 2) for x in res["revenue_per_head"]] == [2.07, 7.94]
    assert [r(100 * x) for x in res["comp_ratio"]] == [45.4, 83.0]
    assert r(100 * res["paid_out"]) == 98.6 and r(res["dividends"]) == 1694.4 and r(res["profit"]) == 1718.4


def test_jane_street():
    js = {(x["entity"], x["year"]): x for x in a.jane_street(S)}
    g, p = a.G, a.L
    assert [r(js[(g, y)]["revenue"]) for y in range(2020, 2026)] == [1567.0, 222.5, 435.0, 383.4, 995.8, 643.0]
    assert [js[(g, y)]["employees"] for y in range(2020, 2026)] == [274, 335, 2, 3, 4, 5]
    assert [r(js[(p, y)]["revenue"]) for y in range(2022, 2026)] == [1230.8, 1286.1, 2271.1, 3875.9]
    assert [r(js[(p, y)]["staff"]) for y in range(2022, 2026)] == [434.9, 494.2, 860.1, 1664.5]
    assert [js[(p, y)]["employees"] for y in range(2022, 2026)] == [483, 636, 688, 790]
    assert r(js[(g, 2021)]["staff"]) == 302.4 and js[(p, 2022)]["months"] == 14
    assert [r(js[(g, y)]["staff_per_head"], 2) for y in (2020, 2021)] == [1.29, 0.90]
    assert [r(js[(p, y)]["staff_per_head"], 2) for y in range(2022, 2026)] == [0.90, 0.78, 1.25, 2.11]
    assert r(js[(p, 2022)]["staff_per_head_annual"], 2) == 0.77
    pat = S.series(g, "ProfitAfterTax")
    assert [r(v / 1e6) for _, v in pat] == [979.1, -69.1, 324.2, 286.5, 654.9, 437.4]
    assert [r(S.get(p, "RevenueFromParent", "2025-12-31") / 1e6), r((3875.901e6 - 2206.628e6) / 1e6)] == [2206.6, 1669.3]


def test_members():
    m = {x["year"]: x for x in a.members(S)}
    assert [r(m[y]["profit"]) for y in range(2022, 2026)] == [667.5, 583.5, 1171.0, 1855.4]
    assert r(m[2025]["profit_to_staff"], 2) == 1.11 and r(m[2025]["per_employee"], 2) == 2.35
    assert round(m[2025]["per_member"]) == 232
    assert r(100 * m[2025]["largest_share"]) == 84.3 and r(100 * m[2024]["largest_share"]) == 90.8
    assert [S.get(a.L, "AverageMembers", f"{y}-12-31") for y in range(2022, 2026)] == [4, 7, 6, 8]


def test_squarepoint():
    s = {x["year"]: x for x in a.squarepoint(S)}
    assert round(s[2025]["charge_per_secondee"], -3) == 659_000 and round(s[2024]["charge_per_secondee"], -3) == 738_000
    assert [r(s[y]["revenue"]) for y in (2024, 2025)] == [106.8, 50.6]
    assert [r(s[y]["profit"]) for y in (2024, 2025)] == [33.6, 1.2]
    assert r(S.get(a.P, "ServiceCharges", "2025-12-31") / 1e6) == 36.2


def test_virtu_fx_barclays():
    v = {x["year"]: x for x in a.virtu(S)}
    ys = range(2020, 2026)
    assert [r(100 * v[y]["comp_ratio"]) for y in ys] == [12.1, 13.4, 16.5, 17.2, 15.1, 14.5]
    assert [r(100 * v[y]["comp_to_trading"]) for y in ys] == [15.8, 17.9, 24.0, 30.3, 23.9, 21.7]
    assert r(v[2025]["staff"] / a.VIRTU_EMPLOYEES_2025, 2) == 0.51
    assert len([f for f in S.facts if f.entity == a.V and f.concept == "Revenue"]) == 6
    fx = a.fx_gbp_usd(2024)
    assert r(fx, 4) == 1.2785
    q25 = [x for x in a.quadrature(S) if x["fy"] == 2025][0]
    assert r(q25["staff_per_head"] * fx, 2) == 4.11
    b = a.barclays()
    assert b["high_earners"] == 717 and r(100 * b["under_2m"]) == 64.4 and b["from_5m"] == 39
    assert r(b["ib_mean"], 2) == 1.56 and r(100 * b["ib_variable_share"]) == 58.0


def test_small_runs():
    sts = a.statements(S)
    assert len(sts) == 6 and all(st.headcount for st in sts)
    assert abs(sts[-1].comp - 556.12e6) < 1 and sts[-1].year == 2025
