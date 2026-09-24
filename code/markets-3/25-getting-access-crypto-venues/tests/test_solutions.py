"""Numbers in the solutions of Book 3, Chapter 25."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import m3_cryptoaccess as m


def test_exercises():
    assert round(m.monthly_fees(100e6, 0.7, m.BINANCE)) == 43_600
    assert round(200_000 / 86_400, 1) == 2.3
    assert round(m.tier_match_value()) == 11_040
    assert round(210e6 * 0.5 / 1e4) == 10_500
    s = m.quoting_snapshots(thin_at=2.5)
    assert (round(m.uptime(s, 10, 50_000), 3), round(m.uptime(s, 20, 50_000), 3)) == (0.640, 0.936)


def test_problem():
    spread, conc = m.spread_vs_concentrate()
    assert {k: round(v) for k, v in spread.items()} == {"Binance": 52_320, "Kraken": 28_800, "C": 43_200, "D": 86_400,
                                                         "E": 110_400}
    assert {k: round(v) for k, v in conc.items()} == {"Binance": 80_400, "Kraken": 63_000}
    assert round(sum(spread.values()) - sum(conc.values())) == 177_720
    assert round(m.programme_value()[0], 3) == 0.873 and round(m.programme_value(thin_at=2.25)[0], 3) == 0.910
