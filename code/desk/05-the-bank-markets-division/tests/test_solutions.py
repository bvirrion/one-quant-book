"""Numbers gate: every numerical answer printed in Book 16, chapter 5 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import fm_bank as m  # noqa: E402

bd = m.bd


def r(x, d=1):
    return round(float(x), d)


def test_published_bank():
    q = m.jpm_requirements()
    assert (r(q["tier1_rwa"]), r(q["tier1_leverage"]), r(q["le_over_rwa"])) == (257.6, 265.1, 2.7)
    j = m.jpm()
    assert r(100 * j["tier1_capital_musd"] / j["total_leverage_exposure_musd"]) == 5.8
    assert r(100 * q["cib_roe_check"]) == 18.6
    assert j["cet1_requirement_pct"] == 4.5 + j["scb_pct"] + j["gsib_method2_pct"]


def test_roae_table():
    t, eq = m.roae_table()
    want = [(15.4, 9.6, 9.6), (53.8, 5.2, 5.2), (23.1, 13.5, 13.5), (18.1, 27.5, 18.1), (28.8, 28.1, 28.1),
            (10.4, 22.5, 10.4)]
    for i, w in enumerate(want):
        assert (r(100 * t["rwa"][i]), r(100 * t["leverage"][i]), r(100 * t["binding"][i])) == w
    assert [bd.binding(d, m.KEYS) for d in m.DESKS] == ["leverage", "leverage", "leverage", "rwa", "leverage", "rwa"]
    d = m.division()
    assert (r(d["equity_rwa"]), r(d["equity_le"]), r(d["equity_binding"]), r(100 * d["roe_binding"])) == (35.1, 55.5, 62.1,
                                                                                                        11.4)
    assert [x.name for i, x in enumerate(m.DESKS) if t["binding"][i] >= 0.12] == ["prime services", "equity derivatives",
                                                                                  "FX"]


def test_charge_and_mix():
    assert r(100 * m.charge_rate(), 2) == 0.6
    c = m.charged_profits()
    assert (r(c["repo"], 2), r(c["prime services"], 2), r(c["equity derivatives"], 2)) == (-0.75, 0.45, 1.11)
    repo = m.DESKS[1]
    assert r(repo.profit(0.25), 2) == 1.05 and r(10000 * bd.breakeven_charge(repo), 0) == 35
    x = m.mix()
    assert r(x[1], 2) == 0.11 and all(r(v, 2) == 1.5 for i, v in enumerate(x) if i != 1)
    assert r(sum(dd.profit(0.25) * xi for dd, xi in zip(m.DESKS, x, strict=True)), 2) == 9.12


def test_franchise():
    f = m.franchise()
    assert (r(f["profit"], 2), r(f["equity"]), r(100 * f["roe"]), r(f["base_profit"], 2)) == (6.08, 50.1, 12.1, 7.05)
    g = m.franchise(prime_loss=0.4)
    assert (r(g["profit"], 3), r(g["equity"]), r(100 * g["roe"])) == (5.625, 48.1, 11.7)
