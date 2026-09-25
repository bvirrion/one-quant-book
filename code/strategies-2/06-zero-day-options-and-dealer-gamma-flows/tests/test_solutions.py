"""Numbers gate: every numerical answer printed in Book 9, chapter 6 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s2_gammaflow import day_vol, estimates, flips, pinning, regimes  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def pct(x, d=1):
    return round(100 * float(x), d)


def test_estimates():
    e = estimates()
    assert (pct(e["convention"]["agree"]), r(e["convention"]["corr"]), pct(e["average sides"]["agree"]),
            r(e["average sides"]["corr"]), pct(e["short_share"]), pct(e["est_short_share"])) == (
        56.0, 0.23, 57.5, 0.24, 56.4, 51.5)


def test_regimes():
    g = regimes()
    got = {k: (r(v["short_mean"]), r(v["short_t"], 1), r(v["long_mean"]), r(v["long_t"], 1), r(v["rule_mean"]),
               r(v["rule_sr"]), r(v["net_sr"])) for k, v in g.items() if k != "unconditional"}
    assert got == {"true": (3.12, 3.0, -3.4, -4.1, 3.24, 1.68, 1.16),
                   "convention": (1.02, 1.0, -0.52, -0.5, 0.78, 0.4, -0.11),
                   "average sides": (1.08, 1.3, -1.77, -1.4, 1.28, 0.66, 0.14)}
    assert (r(g["unconditional"]["mean"]), r(g["unconditional"]["sr"])) == (0.27, 0.14)


def test_vol_pin_flip():
    v, p, f = day_vol(), pinning(), flips()
    assert (r(v["short"]), r(v["long"]), r(v["free"])) == (1.48, 0.81, 0.99)
    assert (pct(p["long"]), pct(p["short"]), pct(p["free"])) == (21.4, 20.4, 21.4)
    assert (pct(f["true_share"]), pct(f["conv_share"]), r(f["conv_median"]), f["strikes"]) == (36.5, 96.0, 100.28, 61)


def test_exercises():
    from s2_gammaflow import no_impact
    n = no_impact()
    assert (r(n["mean"]), r(n["t"], 1), r(n["rule_mean"]), r(n["rule_t"])) == (-1.38, -2.2, 0.03, 0.05)
    g, e = regimes(), estimates()
    assert r(g["convention"]["rule_mean"] / g["true"]["rule_mean"]) == 0.24
    assert pct(1 - e["convention"]["agree"], 0) == 44
    assert (5 * 2, 0.1 / 0.5) == (10, 0.2)
