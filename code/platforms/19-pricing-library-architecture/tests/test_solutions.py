"""Numbers gate: every numerical answer printed in One Quant Book 15, chapter 19 (text and solutions)."""
import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import pl_payoffdsl as P

FIG = pathlib.Path(__file__).resolve().parents[4] / "figdata/platforms/19-pricing-library-architecture"


def _csv(name):
    return list(csv.DictReader(open(FIG / name)))


def test_small_runs():
    s = P.products()["autocallable"][0]
    eng = P.D.ScriptEngine(n_paths=2_000, mode="interpreted")
    fast = P.D.ScriptEngine(n_paths=2_000)
    assert abs(eng.price(s, P.FP.BlackScholes(), P.market()) - fast.price(s, P.FP.BlackScholes(), P.market())) < 1e-9


def test_named_result_numbers():
    v = {r["product"]: r for r in _csv("validation.csv")}
    assert (v["autocallable"]["script"], v["autocallable"]["library"], v["autocallable"]["diff_se"]) \
        == ("95.8750", "95.8750", "0.00")
    assert (v["European call"]["script"], v["European call"]["library"], v["European call"]["diff_se"]) \
        == ("11.3953", "11.3485", "0.82")
    assert v["Asian call"]["diff_se"] == "0.00" and v["down-and-out call"]["diff_se"] == "0.26"
    assert v["autocallable; lookback knock-in"]["script"] == "94.2474" and v["autocallable"]["se"] == "0.0717"
    d = P.deltas()
    assert d["script"] == d["library"] and round(d["script"], 4) == 0.1518
    lz = P.lazy_demo()
    assert (round(lz["first"], 2), round(lz["after"], 2), lz["calculations"]) == (11.35, 11.59, 2)
    sp = {int(r["paths"]): float(r["speedup"]) for r in _csv("measured_speed.csv")}
    assert (sp[1000], sp[30_000], max(sp.values())) == (18.8, 33.4, 34.3)
    assert len(P.AUTOCALL.splitlines()) == 9 and len(P.LOOKBACK.splitlines()) == 11
    assert round(95.8750 - 94.2474, 2) == 1.63


def test_exercises():
    lv = {k: round(v, 2) for k, v in P.lookback_levels().items()}
    assert lv == {0.5: 97.64, 0.6: 94.25, 0.7: 92.28}
    exp = P.EXPIRY
    s = P.D.ScriptedInstrument(id="DG", underlying="A", currency="USD",
                               script="at expiry { if S > 105 { pay 10; } }", dates=(("expiry", (exp,)),))
    d = P.FP.DigitalOption(id="DG", underlying="A", currency="USD", strike=105.0, expiry=exp, right="C", payout=10.0)
    ps = P.FP.price(s, P.market()).pv
    pd = P.FP.price(d, P.market(), engine=P.FP.MonteCarloEngine()).pv
    assert abs(ps - pd) < 1e-9 and round(ps, 2) == 4.09
