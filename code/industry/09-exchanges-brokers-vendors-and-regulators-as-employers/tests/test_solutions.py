"""Numbers gate: every numerical answer printed in Book 17, chapter 9 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import in_infra as m  # noqa: E402


def r(x, d=1):
    return round(float(x), d)


def test_exchanges():
    e = {x["firm"]: x for x in m.exchanges()}
    assert {k: (r(v["revenue_per_head_m"], 2), r(v["op_income_per_head_m"], 2), r(100 * v["op_margin"])) for k, v in e.items()} == {
        "CME Group": (1.68, 1.09, 64.9), "Intercontinental Exchange": (0.98, 0.38, 39.0),
        "Nasdaq": (0.87, 0.24, 28.2), "Cboe Global Markets": (2.84, 0.88, 31.1)}
    assert r(e["CME Group"]["op_income_per_head_m"] / e["Nasdaq"]["op_income_per_head_m"]) == 4.5
    assert (r(5249 / 9525, 2), r(100 * 2331 / 5249)) == (0.55, 44.4)
    assert (r(64.9 - 28.2), r(64.9 - 44.4)) == (36.7, 20.5)


def test_bands():
    ny = {g: tuple(round(x) for x in m.sec_band(g)) for g in (12, 13, 14, 15, 16, 17)}
    assert ny[12] == (115489, 195672) and ny[13] == (137339, 232678) and ny[14] == (157698, 267168)
    assert ny[15] == (167168, 288543) and ny[16] == (180094, 292300) and ny[17][1] == 292300
    assert r(232678 / 137339, 2) == 1.69 and r(ny[14][1] / ny[14][0], 1) == 1.7
    ch = tuple(round(x) for x in m.sec_band(14, "Chicago"))
    assert ch == (149593, 253437) and round(sum(ch) / 2) == 201515 and round(sum(ny[14]) / 2) == 212433
    assert round(sum(ny[14]) / 2) - round(sum(ch) / 2) == 10918


def test_filings():
    fl = m.filings()
    ex = [fl[("exchange", r)] for r in m.ROLES]
    assert [x["p50"] for x in ex] == [130_800, 140_400, 107_100, 108_500] and [x["n"] for x in ex] == [462, 329, 35, 60]
    assert all(x["employers"] == 4 for x in ex)
    assert [fl[("bank", r)]["p50"] for r in m.ROLES] == [154_260, 155_688, 158_100, 140_714]
    assert [fl[("market maker", r)]["p50"] for r in m.ROLES] == [175_000] * 4
    lo, hi = m.sec_band(14)
    assert (round(lo), round(hi)) == (157_698, 267_168)
