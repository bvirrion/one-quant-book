"""Provenance script (network; not run by the tests): derived statistics of the US market's daily excess return
from the Kenneth French data library (Fama/French 3 factors, daily, Mkt-RF), written to data/research/ff_*.csv.

The library carries a copyright notice and no licence, so the raw series is not redistributed: only statistics
computed from it (a histogram, autocorrelations, kurtoses by horizon, leverage correlations, tail estimates and a
summary), which are facts about the series.

    python3 rs_fetch_french.py [F-F_Research_Data_Factors_daily.csv [10_Industry_Portfolios_Daily.csv]]
"""
from __future__ import annotations

import io
import math
import pathlib
import sys
import urllib.request
import zipfile

import numpy as np

URL = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_Factors_daily_CSV.zip"
URL_IND = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/10_Industry_Portfolios_daily_CSV.zip"
ROOT = pathlib.Path(__file__).resolve().parents[4]
OUT = ROOT / "data" / "research"
sys.path.insert(0, str(ROOT / "code" / "firm" / "robust"))
from firm_robust import hill  # noqa: E402


def _text(path, url):
    if path:
        return pathlib.Path(path).read_text()
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    z = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(req).read()))
    return z.read(z.namelist()[0]).decode()


def load_industries(path=None):
    """Value-weighted daily returns of the 10 industry portfolios (first section of the file)."""
    dates, rows = [], []
    for line in _text(path, URL_IND).splitlines():
        if "Equal Weighted" in line:
            break
        parts = [p.strip() for p in line.split(",")]
        if len(parts) == 11 and parts[0].isdigit() and len(parts[0]) == 8:
            dates.append(parts[0])
            rows.append([float(x) / 100.0 for x in parts[1:]])
    return np.array(dates), np.array(rows)


def derive_asymmetry(dates, mkt, idates, ind):
    """Average pairwise correlation of the 10 industries on days the market's excess return is below -c or above +c
    standard deviations, for thresholds c from 0 to 2 (exceedance correlations conditioned on the market)."""
    common, i1, i2 = np.intersect1d(dates, idates, return_indices=True)
    z = mkt[i1] / mkt[i1].std()
    x = ind[i2]
    with open(OUT / "ff_asym.csv", "w") as f:
        f.write("threshold,down,up,n_down,n_up\n")
        for c in (0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0):
            out = []
            for rows in (z < -c, z > c):
                cc = np.corrcoef(x[rows].T)
                out.append(float((cc.sum() - 10) / 90))
            f.write(f"{c},{out[0]:.4f},{out[1]:.4f},{int((z < -c).sum())},{int((z > c).sum())}\n")


def load(path=None):
    text = _text(path, URL)
    dates, mkt = [], []
    for line in text.splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 5 and parts[0].isdigit() and len(parts[0]) == 8:
            dates.append(parts[0])
            mkt.append(float(parts[1]) / 100.0)
    return np.array(dates), np.array(mkt)


def kurt(x):
    x = x - x.mean()
    return float((x**4).mean() / (x**2).mean() ** 2)


def skew(x):
    x = x - x.mean()
    return float((x**3).mean() / (x**2).mean() ** 1.5)


def acf(x, lags):
    x = x - x.mean()
    v = (x * x).mean()
    return np.array([(x[:-k] * x[k:]).mean() / v for k in lags])


def derive(dates, r):
    OUT.mkdir(parents=True, exist_ok=True)
    sd = r.std()
    z = r / sd
    edges = np.arange(-10.25, 10.26, 0.5)
    counts = np.histogram(np.clip(z, -10.24, 10.24), bins=edges)[0]
    centres = 0.5 * (edges[1:] + edges[:-1])
    phi = lambda u: 0.5 * (1 + math.erf(u / math.sqrt(2)))  # noqa: E731
    normal = [len(z) * (phi(b) - phi(a)) for a, b in zip(edges[:-1], edges[1:], strict=True)]
    with open(OUT / "ff_hist.csv", "w") as f:
        f.write("z,count,normal\n")
        for c, n, e in zip(centres, counts, normal, strict=True):
            f.write(f"{c:.2f},{n},{e:.6g}\n")
    lags = np.arange(1, 251)
    a_r, a_abs, a_sq = acf(r, lags), acf(np.abs(r), lags), acf(r * r, lags)
    with open(OUT / "ff_acf.csv", "w") as f:
        f.write("lag,r,abs,sq\n")
        for k, x, y, w in zip(lags, a_r, a_abs, a_sq, strict=True):
            f.write(f"{k},{x:.5f},{y:.5f},{w:.5f}\n")
    with open(OUT / "ff_agg.csv", "w") as f:
        f.write("horizon,n,kurtosis,skewness\n")
        lr = np.log1p(r)
        for h in (1, 5, 10, 21, 63, 126, 252):
            m = len(lr) // h
            agg = lr[: m * h].reshape(m, h).sum(axis=1)
            f.write(f"{h},{m},{kurt(agg):.4f},{skew(agg):.4f}\n")
    with open(OUT / "ff_lev.csv", "w") as f:
        f.write("lag,corr\n")
        r2 = r * r
        for k in range(-20, 21):
            if k >= 0:
                a, b = r[: len(r) - k], r2[k:]
            else:
                a, b = r[-k:], r2[: len(r) + k]
            f.write(f"{k},{np.corrcoef(a, b)[0, 1]:.5f}\n")
    i87 = int(np.flatnonzero(dates == "19871019")[0])
    prior = r[i87 - 5 * 252: i87]
    left, _ = hill(-r, 500)
    right, _ = hill(r, 500)
    rows = {
        "first": dates[0], "last": dates[-1], "n": len(r), "mean_pct": 100 * r.mean(), "sd_pct": 100 * sd,
        "kurtosis": kurt(r), "skewness": skew(r),
        "min_pct": 100 * r.min(), "min_date": dates[int(np.argmin(r))],
        "max_pct": 100 * r.max(), "max_date": dates[int(np.argmax(r))],
        "r_19871019_pct": 100 * r[i87], "sd_prior5y_pct": 100 * prior.std(), "sigmas_1987": r[i87] / prior.std(),
        "days_beyond_5sd": int((np.abs(z) > 5).sum()), "normal_beyond_5sd": len(z) * 2 * (1 - phi(5.0)),
        "hill_left_k500": left, "hill_right_k500": right,
        "acf_abs_1": a_abs[0], "acf_abs_20": a_abs[19], "acf_abs_100": a_abs[99], "acf_r_1": a_r[0],
    }
    with open(OUT / "ff_summary.csv", "w") as f:
        f.write("key,value\n")
        for k, v in rows.items():
            f.write(f"{k},{v if isinstance(v, (str, int, np.integer, np.str_)) else f'{v:.6g}'}\n")


if __name__ == "__main__":
    d, m = load(sys.argv[1] if len(sys.argv) > 1 else None)
    derive(d, m)
    derive_asymmetry(d, m, *load_industries(sys.argv[2] if len(sys.argv) > 2 else None))
