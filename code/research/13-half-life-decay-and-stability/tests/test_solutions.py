"""Numbers gate: every numerical answer printed in Book 7, chapter 13 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from rs_decay import (
    BROKEN,
    CUT,
    MarketConfig,
    decay_table,
    detection,
    factors,
    monthly_ic,
    posterior_curve,
    power,
    stability,
)


def r(x, d=3):
    return round(float(x), d)


# Printed digits that move with the CPU's floating-point kernels: skipped by CI (make test-fast).
@pytest.mark.reference
def test_decay_table():
    d = decay_table()
    assert [r(d[k]["ic"][1]) for k in ("reversal", "surprise", "momentum", "book-to-price")] == [0.037, 0.010, 0.008, 0.004]
    assert [r(d[k]["rho"], 4) for k in ("surprise", "book-to-price")] == [0.9826, 0.9995]
    assert (r(d["reversal"]["rho"], 2), r(d["momentum"]["rho"])) == (-0.04, 0.995)
    assert d["reversal"]["curve_half_life"] < 1 and round(d["surprise"]["curve_half_life"]) == 20
    assert d["momentum"]["curve_half_life"] >= 2000
    assert [round(d[k]["signal_half_life"]) for k in ("surprise", "momentum", "book-to-price")] == [39, 130, 1386]
    assert [round(100 * (1 - d[k]["rho"]), 2) for k in ("reversal", "surprise", "momentum", "book-to-price")] == [
        104.24, 1.74, 0.53, 0.05]
    assert d["surprise"]["ic"][60] < 0.0 < d["surprise"]["ic"][40]


def test_stability_and_breaks():
    m = stability("momentum")
    assert (r(m["mean"]), r(m["sd"]), m["n"]) == (0.023, 0.247, 95)
    assert (r(min(m["yearly"]), 2), r(max(m["yearly"]), 2)) == (-0.11, 0.18)
    assert (r(m["ci"][0]), r(m["ci"][1])) == (-0.035, 0.071)
    assert m["cusum_first"] == m["n"] - 1 and r(m["supf_p"]) == 0.023
    s = stability("surprise")
    assert (r(s["mean"], 3), r(s["sd"], 3)) == (0.040, 0.041)
    assert (r(min(s["yearly"]), 2), r(max(s["yearly"]), 2)) == (0.02, 0.06)
    b = stability("surprise", BROKEN)
    x = monthly_ic("surprise", cfg=BROKEN)
    assert (r(x[:48].mean()), r(x[51:].mean())) == (0.032, 0.005)
    assert (r(b["supf"], 1), b["supf_at"], r(b["supf_p"])) == (12.5, 53, 0.013)
    assert b["cusum_first"] == -1 and r(b["cusum_max"], 2) == 0.69
    c = stability("surprise", CUT)
    assert r(c["supf_p"], 2) == 0.93 and c["cusum_first"] == -1


def test_detection_power():
    assert detection(0.0) == (1.0, 0.5)
    assert detection(0.3) == (0.7, 0.3)
    assert detection(0.5) == (0.3, 0.1)
    assert detection(1.0) == (0.1, 0.1)


def test_factors():
    f = factors().set_index(["factor", "period"])
    before = [f.loc[(k, "before")] for k in ("SMB", "HML", "Mom")]
    after = [f.loc[(k, "after")] for k in ("SMB", "HML", "Mom")]
    assert [r(100 * x["mean"], 2) for x in before] == [0.47, 0.42, 0.85]
    assert [r(100 * x["mean"], 2) for x in after] == [0.01, 0.19, 0.37]
    assert [r(x["t"], 2) for x in before] == [2.25, 3.12, 4.76] and [r(x["t"], 2) for x in after] == [0.10, 1.16, 1.54]
    assert [round(100 * (1 - a["mean"] / b["mean"])) for a, b in zip(after, before, strict=True)] == [97, 55, 56]
    assert [r(f.loc[(k, "break")]["t"], 3) for k in ("SMB", "HML", "Mom")] == [0.176, 0.153, 0.053]
    assert before[0]["start"] == "1963-07" and after[0]["end"] == "2026-07"


def test_power():
    mom_t = 0.023 / 0.247 * math.sqrt(60)
    p = power(0.023, 0.247)
    assert (r(mom_t, 2), r(p["luck"], 2), r(p["decay"], 2), r(p["posterior"], 2)) == (0.72, 0.37, 0.50, 0.57)
    f = factors().set_index(["factor", "period"]).loc[("Mom", "before")]
    t_mom = f["mean"] / f["sd"] * math.sqrt(60)
    assert (r(t_mom, 2), r(power(f["mean"], f["sd"])["posterior"], 2)) == (1.93, 0.72)
    s = power(0.0397, 0.0407)
    assert (r(0.0397 / 0.0407 * math.sqrt(60), 1), r(s["posterior"])) == (7.6, 0.999)
    curve = posterior_curve()
    assert (r(curve[3.0], 3), r(curve[4.0], 3)) == (0.849, 0.932)
    phi = lambda z: 0.5 * (1 + math.erf(z / math.sqrt(2)))  # noqa: E731
    assert (r(phi(-mom_t / math.sqrt(5)), 2), r(phi(-t_mom / math.sqrt(5)), 2)) == (0.37, 0.19)
    assert r(phi(-0.0397 / 0.0407 * math.sqrt(60) / math.sqrt(5)), 4) == 0.0004
    p0 = 0.5 / 0.9 - 0.5
    assert r(p0, 3) == 0.056
    t90 = next(t / 100 for t in range(100, 800) if phi(-t / 100 / math.sqrt(5)) <= p0)
    assert round(t90, 1) == 3.6


def test_exercises():
    assert (r(-math.log(2) / math.log(0.98), 1), r(1 - 0.98, 2)) == (34.3, 0.02)
    assert round(100 * (1 - 0.37 / 0.85)) == 56
    k = 94
    assert (r(0.948 * (math.sqrt(k) + 2 / math.sqrt(k)), 2), r(0.948 * (math.sqrt(k) + 2 * k / math.sqrt(k)), 2)) == (9.39, 27.57)
    assert [(60 - h) / 60 for h in (0, 30, 60)] == [1.0, 0.5, 0.0]
    t = 0.04 / (0.10 / math.sqrt(60))
    assert (r(t, 2), r(power(0.04, 0.10)["posterior"], 3)) == (3.10, 0.858)
    assert isinstance(MarketConfig(), MarketConfig) and np.isfinite(t)
