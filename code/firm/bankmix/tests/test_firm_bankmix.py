import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_bankmix as bm  # noqa: E402


def rows():
    return [bm.Row("A", 2025, 60, 40, "USD", "F1", ""), bm.Row("B", 2025, 20, 80, "EUR", "F2", ""),
            bm.Row("A", 2024, 70, 30, "USD", "F1", "")]


def test_shares_and_order():
    t = bm.mix_table(rows(), 2025)
    assert t[0][0] == "B" and abs(t[0][1] - 0.8) < 1e-12 and abs(bm.mix_change(rows(), "A", 2024, 2025) - 10) < 1e-9


def test_fx_and_top_k(tmp_path):
    p = tmp_path / "fx.csv"
    p.write_text("year,usd_per_eur,gbp_per_eur\n2025,1.2,0.8\n")
    fx = bm.load_fx(p)
    assert abs(fx[2025]["GBP"] - 1.5) < 1e-12 and bm.to_usd(rows()[1], fx) == (24.0, 96.0)
    assert abs(bm.top_k_equities_share(rows(), fx, 2025, 1) - 96 / 136) < 1e-12


def test_load_roundtrip(tmp_path):
    p = tmp_path / "r.csv"
    p.write_text("bank,year,ficc,equities,currency,ledger,lines\nA,2025,1,2,USD,F1,x\n")
    assert bm.load(p)[0].equities == 2.0
