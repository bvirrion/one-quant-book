"""Numbers gate: every numerical answer printed in One Quant Book 15, chapter 22 (text and solutions)."""
import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import pl_posttrade as P

FIG = pathlib.Path(__file__).resolve().parents[4] / "figdata/platforms/22-post-trade-systems"


def _csv(name):
    return list(csv.DictReader(open(FIG / name)))


def test_small_runs():
    o = P.trades(0, 1, n=40)
    t, planted = P.confirms(o)
    assert len(t) == 40 - sum(1 for k in planted.values() if k == "missing")
    fixed, failed = P.resolve(P.breaks(o, t), "T+1")
    assert len(fixed) + len(failed) == len(P.breaks(o, t))


def test_match_rates():
    rows = {f"{tol:g}": (round(100 * r, 1), p, a, b) for tol, r, p, a, b in P.match_rates(tols=(0.0, 1e-5, 1e-4, 5e-2))}
    assert rows == {"0": (60.4, 193, 5, 0), "1e-05": (67.6, 157, 5, 0), "0.0001": (95.8, 16, 5, 0),
                    "0.05": (96.8, 11, 5, 0)}
    assert [r["rate_pct"] for r in _csv("match_rate.csv")] == ["60.4", "61.0", "67.6", "95.8", "95.8", "95.8", "95.8",
                                                               "96.8"]


def test_instruction():
    o = P.trades(0, 1)[0]
    ssi = P.PT.SSITable({(b, "US"): {"agent": "AGT" + b[-1], "account": "ACC-" + b} for b in P.BROKERS})
    ins = ssi.instruction(o, "OUR-" + o["fund"])
    assert (ins["type"], ins["quantity"], ins["amount"], ins["their_account"]) == (
        "deliver versus payment", 9400, 917317.25, "ACC-BRK2")


def test_cycles_and_ageing():
    w2, w1 = P.week("T+2"), P.week("T+1")
    assert (w2["breaks"], w2["failed"], round(w2["failed_value"] / 1e6, 2)) == (138, 10, 2.74)
    assert (w1["breaks"], w1["failed"], round(w1["failed_value"] / 1e6, 2)) == (138, 47, 19.17)
    assert w1["by_kind"] == {"account": 18, "missing": 18, "price": 6, "qty": 3, "settle_date": 2}
    r2, r1 = P.custodian_recon("T+2"), P.custodian_recon("T+1")
    assert (r2["breaks"], r1["breaks"]) == (4, 24)
    assert list(r1["ageing"].values()) == [7, 12, 5, 0] and list(r2["ageing"].values()) == [0, 4, 0, 0]
    assert _csv("cycles.csv")[1]["failed_value_m"] == "19.17"


def test_staffing_csv():
    rows = [(r["staff"], r["failed"], r["failed_half_errors"]) for r in _csv("staffing.csv")]
    assert rows == [("3", "47", "13"), ("4", "35", "9"), ("5", "22", "7"), ("6", "14", "5"), ("7", "11", "4"),
                    ("8", "10", "4")]
    assert P.week("T+1", staff=7)["failed"] == 11
    k = {r["kind"]: int(r["breaks"]) for r in _csv("kinds.csv")}
    assert k == {"account": 43, "missing": 32, "settle_date": 27, "price": 26, "qty": 10}
