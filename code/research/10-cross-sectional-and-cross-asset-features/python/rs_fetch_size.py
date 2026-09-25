"""Derived lead-lag statistics of US size portfolios (One Quant Book 7, chapter 10).

Downloads the Kenneth R. French Data Library file "Portfolios Formed on Size [Daily]" and writes only statistics
computed from it to data/research/ff_size_leadlag.csv (the library carries a copyright notice and no licence, so the
series itself is not stored): for the equal- and value-weighted smallest and largest size quintiles, over three
periods, at daily and weekly (Wednesday to Wednesday) frequency, the cross-autocorrelations at one lag in both
directions, the own first-order autocorrelations, and the regression of the small quintile's return on its own
previous return and the large quintile's previous return (coefficient and t statistic of the latter). Run once;
the chapter's tests read the CSV.
"""
from __future__ import annotations

import io
import pathlib
import urllib.request
import zipfile

import numpy as np
import pandas as pd

URL = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/Portfolios_Formed_on_ME_daily_CSV.zip"
OUT = pathlib.Path(__file__).resolve().parents[4] / "data" / "research" / "ff_size_leadlag.csv"
PERIODS = (("1962-07-01", "1987-12-31"), ("1988-01-01", "2006-12-31"), ("2007-01-01", "2026-12-31"))


def sections(text: str) -> dict[str, pd.DataFrame]:
    lines = text.splitlines()
    out = {}
    for i, line in enumerate(lines):
        if "Average" in line and "Daily" in line:
            rows, j = [], i + 2
            while j < len(lines) and lines[j].strip()[:1].isdigit():
                rows.append(lines[j])
                j += 1
            df = pd.read_csv(io.StringIO(lines[i + 1] + "\n" + "\n".join(rows)), index_col=0)
            df.index = pd.to_datetime(df.index.astype(str))
            df.columns = [c.strip() for c in df.columns]
            out["EW" if "Equal" in line else "VW"] = df / 100.0
    return out


def stats(small: np.ndarray, big: np.ndarray) -> dict:
    X = np.column_stack([np.ones(len(small) - 1), small[:-1], big[:-1]])
    y = small[1:]
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    res = y - X @ b
    cov = res.var(ddof=3) * np.linalg.inv(X.T @ X)
    return {"small_on_big": np.corrcoef(small[1:], big[:-1])[0, 1],
            "big_on_small": np.corrcoef(big[1:], small[:-1])[0, 1],
            "own_small": np.corrcoef(small[1:], small[:-1])[0, 1], "own_big": np.corrcoef(big[1:], big[:-1])[0, 1],
            "partial_coef": b[2], "partial_t": b[2] / np.sqrt(cov[2, 2]), "n": len(small)}


def main() -> None:
    raw = urllib.request.urlopen(URL, timeout=60).read()
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        text = z.read(z.namelist()[0]).decode("latin-1")
    rows = []
    for w, df in sections(text).items():
        for a, b in PERIODS:
            d = df.loc[a:b, ["Lo 20", "Hi 20"]]
            for freq, x in (("daily", d), ("weekly", (1.0 + d).resample("W-WED").prod() - 1.0)):
                s = stats(x["Lo 20"].to_numpy(), x["Hi 20"].to_numpy())
                rows.append({"weighting": w, "start": a[:4], "end": min(b[:4], str(df.index[-1].year)), "freq": freq,
                             **{k: (round(float(v), 4) if k != "n" else v) for k, v in s.items()}})
    pd.DataFrame(rows).to_csv(OUT, index=False)


if __name__ == "__main__":
    main()
