"""Numbers gate: every numerical answer printed in Book 11, chapter 29 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import hf_venues as h  # noqa: E402


def pct(a, b):
    return round(100 * a / b)


def test_home_errors_and_arithmetic():
    e = h.home_errors()
    broken = {k for k, v in e.items() if v}
    assert broken == {"crypto", "fx_ecn"}
    assert any("not paced" in x for x in e["crypto"]) and any("lot" in x for x in e["fx_ecn"])
    assert 0.125 * 1200 + 5 == 155 and 2 / 0.125 == 16                       # exercises 1 and 2
    top = min(0.4 * 1000, 200)
    assert top == 200 and math.floor(500 * (1000 - top) / 4800) == 83         # exercise 3
    assert round(200_000 / 86_400 / 0.125) == 19 and round(200_000 / 86_400 / 18, 3) == 0.129   # about eighteen, one every ~8 s


def test_playbook_table():
    pb = h.playbook()
    for k in ("lit", "inverted", "bump", "futures_fifo"):
        a = pb[k]["home"]
        assert (round(a["volume"]), pct(a["picked"], a["volume"]), round(a["edge"], 2), round(a["messages"])) == (14567, 42, 0.03, 591)
        assert pb[k]["own"] == a
    lit, inv = pb["lit"]["home"], pb["inverted"]["home"]
    assert (round(lit["fees_ticks"] / 100), round(inv["fees_ticks"] / 100)) == (-29, 15)       # $ over 20 minutes
    b = pb["batch"]["home"]
    assert (round(b["volume"]), b["picked"], round(b["edge"], 2), round(b["messages"]), b["takes"]) == (2567, 0, -1.12, 330, 0)
    fh, fo = pb["futures_pr"]["home"], pb["futures_pr"]["own"]
    assert (round(fh["volume"]), round(fo["volume"]), round(fo["volume"] / fh["volume"], 1)) == (10884, 40633, 3.7)
    assert (pct(fh["picked"], fh["volume"]), pct(fo["picked"], fo["volume"])) == (47, 58)
    assert (round(fh["edge"], 2), round(fo["edge"], 2), round(fh["messages"]), round(fo["messages"])) == (-0.17, -0.14, 474, 419)
    ch, co = pb["crypto"]["home"], pb["crypto"]["own"]
    assert (round(ch["orders"]), round(ch["rejects"]), pct(ch["rejects"], ch["orders"])) == (2735, 2581, 94)
    assert (round(co["orders"]), co["rejects"], round(co["volume"]), round(ch["volume"])) == (118, 0, 8333, 7267)
    assert (pct(ch["picked"], ch["volume"]), pct(co["picked"], co["volume"]), round(ch["edge"], 2), round(co["edge"], 2)) == (56, 48, -0.07, -0.17)
    assert (round(ch["messages"]), round(co["messages"])) == (2857, 191)
    eh, eo = pb["event"]["home"], pb["event"]["own"]
    assert (round(eh["volume"]), round(eo["volume"]), round(100 * eh["picked"] / eh["volume"], 1)) == (8367, 7900, 5.6)
    assert (pct(eo["picked"], eo["volume"]), pct(eh["takes"], eh["volume"]), pct(eo["takes"], eo["volume"])) == (4, 52, 34)
    assert (round(eh["edge"], 2), round(eo["edge"], 2), round(eh["messages"]), round(eo["messages"])) == (-0.52, -0.57, 799, 238)
    assert (pct(eh["messages"] - eo["messages"], eh["messages"]), pct(eh["volume"] - eo["volume"], eh["volume"])) == (70, 6)
    assert pct(fh["volume"], fo["volume"]) == 27                                                  # "a quarter"


def test_budget_curve():
    c = {r["gap"]: r for r in h.budget_curve()}
    assert sorted(round(c[g]["orders"] - c[g]["rejects"]) for g in (0, 2, 4, 8)) == [151, 154, 154, 154]
    best = max(c.values(), key=lambda r: r["volume"])
    assert (best["gap"], round(best["volume"]), round(best["rejects"])) == (8, 10100, 28)
    assert round(c[16]["orders"]) == 118 and c[16]["rejects"] == 0
    assert round(1 - c[16]["volume"] / best["volume"], 3) == 0.175                           # "a sixth"
