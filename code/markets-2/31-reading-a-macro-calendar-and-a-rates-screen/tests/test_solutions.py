"""Numbers gate: every numerical answer printed in Book 2, Chapter 31 (text and solutions)."""
import datetime as dt
import pathlib
import random
import sys
from collections import Counter

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/macrocal"))
from firm_macrocal import blackout, classify, curve_summary, sensitivity, steepener_pnl
from macro_demo import event_stats, payroll_moves, problem, screen, september_2026, surprise_regression

E = event_stats()
P = problem()
M = payroll_moves()


def test_text():
    assert (E["n_on"], E["n_off"], round(E["on2"], 1), round(E["off2"], 1)) == (44, 887, 10.2, 4.6)
    assert (round(E["on2"] / E["off2"], 1), round(E["on10"] / E["off10"], 1), round(E["on_s"] / E["off_s"], 1)) == (2.2, 1.7, 1.4)
    assert [b for _, b in september_2026()] == [False, True, True]
    assert blackout(dt.date(2026, 9, 15), dt.date(2026, 9, 16)) == (dt.date(2026, 9, 5), dt.date(2026, 9, 17))
    r = surprise_regression()
    assert (round(r["b2"], 1), round(r["b10"], 1), round(r["se2"], 1), round(r["se10"], 1)) == (8.4, 5.1, 0.2, 0.2)
    assert (round(P["dv01_10"], 4), round(P["dv01_2"], 4), round(P["dv01"])) == (0.0772, 0.0183, 77_168)
    assert round(P["long_two"] / 1e6) == 421
    kinds = Counter(k for *_, k in M)
    assert (kinds["bull steepening"], kinds["bear flattening"]) == (14, 20)
    days = {d: (d2, d10) for d, d2, d10, _ in M}
    assert tuple(round(x) for x in days["2024-08-02"]) == (-28, -19) and tuple(round(x) for x in days["2024-10-04"]) == (23, 13)
    s = screen()
    assert [round(s["2025-09-22"][k]) for k in ("2s10s", "5s30s", "2s5s10s")] == [54, 106, -34]
    assert [round(s["2026-09-22"][k]) for k in ("2s10s", "5s30s", "2s5s10s")] == [25, 46, -1]


def test_exercises():
    assert blackout(dt.date(2026, 10, 27), dt.date(2026, 10, 28)) == (dt.date(2026, 10, 17), dt.date(2026, 10, 29))
    assert classify(-10, -4) == "bull steepening"
    assert steepener_pnl(50_000, -15, -5) == 500_000 and steepener_pnl(50_000, -10, -10) == 0
    ses = []
    for rep in range(200):
        rng = random.Random(rep)
        z = [rng.gauss(0, 1) for _ in range(36)]
        ses.append(sensitivity(z, [8 * x + rng.gauss(0, 3) for x in z])[1])
    assert round(sum(ses) / len(ses), 2) == 0.51 and round(3 / 36 ** 0.5, 2) == 0.5
    assert max(abs(d2) for _, d2, _, _ in M) == 30.0 or round(max(abs(d2) for _, d2, _, _ in M)) == 30
    assert curve_summary(3.61, 3.71, 4.15, 4.77)["5s30s"] > 105


def test_problem():
    assert (round(P["first_2024-08-02"]), round(P["full_2024-08-02"])) == (694_512, 688_510)
    assert (round(P["first_2024-10-04"]), round(P["full_2024-10-04"])) == (-771_680, -772_969)
    worst = max(M, key=lambda m: abs(m[2] - m[1]))
    assert worst[0] == "2025-08-01" and round(worst[2] - worst[1]) == 11
    assert round(500_000 / 11, -3) == 45_000 and round(P["dv01"] * 11, -4) == 850_000
    assert round(E["on2"], 1) == 10.2
