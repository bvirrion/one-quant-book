"""Numbers gate: every numerical answer printed in Book 17, chapter 7 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import in_banks as b  # noqa: E402

bm = b.bm


def r(x, d=1):
    return round(float(x), d)


def test_mix_2025():
    m = [(k, r(100 * v)) for k, v in b.mix(2025)]
    assert m == [("Morgan Stanley", 64.2), ("Societe Generale", 60.8), ("Goldman Sachs", 53.2), ("BNP Paribas", 42.3),
                 ("Bank of America", 41.2), ("Barclays", 37.3), ("JPMorgan Chase", 37.0), ("Citigroup", 26.1),
                 ("Deutsche Bank", 0.0)]


def test_2023_and_changes():
    rows = b.rows()
    s23 = {x.bank: r(100 * bm.equities_share(x)) for x in rows if x.year == 2023}
    assert s23 == {"JPMorgan Chase": 31.4, "Goldman Sachs": 48.7, "Morgan Stanley": 56.5, "Citigroup": 21.6}
    ch = {k: r(v[2]) for k, v in b.changes().items() if v[0] == 2023}
    assert ch == {"Citigroup": 4.5, "Goldman Sachs": 4.5, "JPMorgan Chase": 5.6, "Morgan Stanley": 7.7}
    assert (r(100 * (15631 / 9986 - 1)), r(100 * (8716 / 7673 - 1))) == (56.5, 13.6)


def test_dollars_and_concentration():
    u = b.usd(2025)
    assert r(sum(a + e for a, e in u.values()) / 1000) == 173.9 and r(sum(e for _, e in u.values()) / 1000) == 72.7
    assert r(100 * b.top3()) == 49.9
    fx = b.fx()[2025]
    assert r(fx["GBP"], 4) == 1.3189 and r(5429 * fx["GBP"], 0) == 7160
    assert (r(u["Societe Generale"][1] / 1000, 2), r(u["BNP Paribas"][1] / 1000, 2)) == (4.11, 4.57)


def test_counterfactual_exercise_7():
    rows = [x if x.bank != "Deutsche Bank" else bm.Row(x.bank, x.year, x.ficc, 3000, x.currency, x.ledger, x.lines)
            for x in b.rows()]
    assert r(100 * bm.top_k_equities_share(rows, b.fx(), 2025, 3)) == 47.7 and r(100 * 3 / 12.6) == 23.8
    assert r(3000 * b.fx()[2025]["EUR"] / 1000, 2) == 3.39
