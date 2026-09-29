"""Numbers gate: every numerical answer printed in One Quant Book 15, chapter 14 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import pl_roofline as P

R = P.R


def test_small_runs():
    cpu = R.Roof("core", 50e9, 20e9)
    assert P.request(cpu, 1)["speedup"] < 1 < P.request(cpu, 10_000)["speedup"]
    assert P.overnight(cpu)["speedup"] > 10 and P.break_even(cpu) is not None
    k = R.k_exposure(20, 5, 7)
    assert k.flops == 20 * 5 * 7 + 2 * 20 * 5


def test_roofs_and_kernels():
    cpu = P.cpu_roof()
    assert (round(cpu.peak / 1e9, 1), round(cpu.bandwidth / 1e9, 1), round(cpu.ridge, 2)) == (66.9, 24.0, 2.79)
    assert round(P.DEV.ridge, 1) == 10.1 and round(P.DEV.peak / cpu.peak) == 508
    assert round(P.DEV.bandwidth / cpu.bandwidth) == 140
    k = {r["kernel"]: r for r in P.kernels_measured()}
    got = {n: float(r["gflops"]) for n, r in k.items()}
    assert (round(got["path step"], 2), round(got["basket payoff"], 2), round(got["exposure aggregation"], 2)) \
        == (0.65, 4.82, 2.63)
    frac = {n: got[n] / (cpu.attainable(float(k[n]["intensity"])) / 1e9) for n in got}
    assert [round(100 * frac[n]) for n in ("path step", "basket payoff", "exposure aggregation", "matrix product")] \
        == [16, 81, 87, 96]


def test_named_result_numbers():
    cpu = P.cpu_roof()
    o = P.overnight(cpu)
    assert (round(o["bytes"] / 1e9), round(o["flops"] / 1e9)) == (98, 66)
    assert (round(o["cpu_s"], 2), round(o["dev_s"] * 1e3, 1), round(o["speedup"]), round(o["amdahl"], 1)) \
        == (4.09, 29.3, 140, 17.6)
    r = P.request(cpu)
    assert (round(r["cpu_s"] * 1e6, 2), round(r["dev_s"] * 1e6, 1), round(1 / r["speedup"])) == (0.33, 10.0, 30)
    assert P.break_even(cpu) == 31 and P.launch_sensitivity(cpu) == [(1e-6, 4), (5e-6, 16), (1e-5, 31), (5e-5, 155)]
    big = P.request(cpu, 10 ** 6)["speedup"]
    assert round(big, 1) == 32.7
    # the asymptote: per trade, the CPU's time against the link's transfer and the device's memory time
    per_dev = P.REQUEST_BYTES / P.DEV.link + 0.8 * P.REQUEST_FLOPS / P.DEV.bandwidth
    assert round((0.8 * P.REQUEST_FLOPS / cpu.bandwidth) / per_dev, 1) == 32.7


def test_exercises():
    cpu = P.cpu_roof()
    assert P.break_even_shared(cpu) == 56
    assert (round(R.amdahl(0.95, 140), 1), round(R.amdahl(0.99, 140), 1)) == (17.6, 58.6)
    assert (int(12 * cpu.ridge) + 1, int(12 * P.DEV.ridge) + 1) == (34, 122)
    assert round(10 * 60 / 140, 1) == 4.3
