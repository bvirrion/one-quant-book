"""Numbers gate: every numerical answer printed in Book 17, chapter 16 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import in_trader as a  # noqa: E402

fr = a.fr


def test_pay():
    cells, o = a.pay()
    mm, bk = cells["all"]["market maker"], cells["all"]["bank"]
    assert (mm["p50"], mm["n"], mm["employers"], mm["p25"], mm["p75"]) == (195_000, 65, 9, 150_000, 250_000)
    assert (bk["p50"], bk["n"], bk["employers"], bk["p25"], bk["p75"]) == (235_000, 58, 5, 152_500, 282_500)
    assert cells["all"]["systematic fund"]["suppressed"] and cells["all"]["multi-manager platform"]["suppressed"]
    assert (int(o["p50"]), int(o["p10"]), int(o["p90"])) == (103_030, 55_130, 309_440)


def test_capacity_and_tails():
    one, five = a.capacity()
    assert one == {0.5: 15, 1.0: 7, 2.0: 3, 4.0: 1} and five[1.0] == 71
    t = {n: (m, s) for n, m, s in a.tails()}
    assert round(100 * t[7][0], 2) == 0.89 and round(100 * t[8][0], 2) == 1.03
    assert round(100 * t[7][1], 2) == 1.37
    assert round(7 / 120, 4) == 0.0583 and round(math.exp(-113 / 60), 3) == 0.152


def test_exercises():
    assert round(120 * 0.01 * math.exp(2), 1) == 8.9
    n = 0
    while fr.mmc_wait_tail(2, (n + 1), 120.0, 1 / 60) <= 0.01:
        n += 1
    assert n == 76
    assert round(100 * fr.mmc_wait_tail(2, 76, 120.0, 1 / 60), 2) == 0.99
    assert round(100 * fr.mmc_wait_tail(2, 77, 120.0, 1 / 60), 2) == 1.03
    assert round(100 * fr.mm1_wait_tail(60, 120, 1 / 60), 1) == 18.4
    assert 0.5 / (120 - 60) * 3600 == 30


def test_small_runs():
    s = fr.lindley_tail(7 / 3600, a.lognormal, 60, 20_000, a.np.random.default_rng(1))
    assert 0 <= s < 0.05


def test_pooling_example():
    def cap(c):
        n = 0
        while fr.mmc_wait_tail(c, (n + 1), 120.0, 1 / 60) <= 0.01:
            n += 1
        return n
    assert [cap(c) for c in (1, 2, 3)] == [7, 76, 174]
    assert -(-40 // 7) == 6 and round(100 * fr.mmc_wait_tail(2, 40, 120, 1 / 60), 2) == 0.17
    assert fr.mmc_wait_tail(1, 40, 120, 1 / 60) > 0.01
    c = fr.card("trader")
    assert c.soc_codes == ("13-2099.01", "13-2051", "41-3031") and c.pnl == "owns"
