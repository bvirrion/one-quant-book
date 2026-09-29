"""One Quant Book 17, chapter 5: multi-manager platforms from the employee's side.

Two readings: the platforms' Form ADV panel (data/industry/adv_platforms.csv, derived by in_platform_derive.py), and
team tenure under drawdown ladders (firm.teamtenure). The ladders, the teams' volatility and their Sharpe ratios are
illustrative parameters, not any platform's terms.
"""
import csv
import functools
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/teamtenure"))
import firm_teamtenure as tt  # noqa: E402

DATA = ROOT / "data/industry"
VOL = 0.10                                   # annual volatility of a team's P&L on its allocated capital
TIGHT, LOOSE = tt.Ladder(0.05, 0.075), tt.Ladder(0.10, 0.15)
SRS = (0.0, 0.5, 1.0, 1.5)                   # the mixed population: one quarter of teams at each true Sharpe ratio
YEARS = 10


def panel():
    with open(DATA / "adv_platforms.csv") as f:
        return [dict(r, employees=float(r["employees"]), advisory=float(r["advisory"]), raum_bn=float(r["raum_bn"]))
                for r in csv.DictReader(f)]


def growth(platform, first, last):
    rows = {r["file"]: r for r in panel() if r["platform"] == platform}
    a, b = rows[first], rows[last]
    return dict(employees=b["employees"] / a["employees"], raum=b["raum_bn"] / a["raum_bn"],
                raum_per_employee=(b["raum_bn"] / b["employees"]) / (a["raum_bn"] / a["employees"]),
                advisory_share=(a["advisory"] / a["employees"], b["advisory"] / b["employees"]))


@functools.cache
def times(sr, ladder, n=4000, years=YEARS, seed=0):
    return tt.stop_times(sr, VOL, ladder, n, years, np.random.default_rng(seed + int(100 * sr)))


def table(n=4000):
    out = {}
    for name, lad in (("tight", TIGHT), ("loose", LOOSE)):
        for sr in SRS:
            t = times(sr, lad, n)
            out[(name, sr)] = dict(median=tt.median_tenure(t), stopped=float(np.isfinite(t).mean()),
                                   s1=float(tt.survival(t, [1.0])[0]), s3=float(tt.survival(t, [3.0])[0]),
                                   turnover=tt.turnover(t, YEARS))
    return out


def mixed(ladder, n=4000):
    ts = {sr: times(sr, ladder, n) for sr in SRS}
    allt = np.concatenate(list(ts.values()))
    return dict(turnover=tt.turnover(allt, YEARS), median=tt.median_tenure(allt),
                false_cut=tt.false_cut_share(ts, {1.0, 1.5}),
                first_year_stops=float((allt <= 1.0).mean()))
