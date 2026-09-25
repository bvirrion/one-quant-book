"""FX flow strategies (One Quant Book 9, chapter 15).

Synthetic: firm.fxflows's thirty years of month-ends: foreign holders of home equities (hedge ratio 0.5) and home
holders of foreign equities (0.3) rebalance their currency hedges at month-end; the flow moves the rate before the
fix (0.065 per unit of flow) and half of it reverses after; the trader estimates the flow with 30% errors in holdings
and hedge ratios and trades ahead of it; a liquidity provider takes the other side of the fix-window push. Real: the
dollar over the last days of each month against the S&P 500's month, 1999-2026, as derived statistics. NumPy.
"""
from __future__ import annotations

import csv
import functools
import math
import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "firm" / "fxflows"))
from firm_fxflows import FlowFXConfig, fix_liquidity, flow_trade, simulate_months  # noqa: E402

DATA = ROOT.parent / "data" / "strategies-2"


@functools.lru_cache(maxsize=1)
def months():
    cfg = FlowFXConfig()
    return cfg, simulate_months(cfg)


def _t(x):
    return float(x.mean() / x.std(ddof=1) * math.sqrt(len(x)))


def results():
    cfg, s = months()
    p, f = flow_trade(s, cfg), fix_liquidity(s, cfg)
    q = np.quantile(np.abs(s["est"]), [0.2, 0.4, 0.6, 0.8])
    g = np.digitize(np.abs(s["est"]), q)
    after = 1e4 * -np.sign(s["est"]) * s["after"] - cfg.cost_bp
    est_bp = np.abs(s["est"]) * cfg.impact * 1e4
    return {"push_sd": float((cfg.impact * s["flow"]).std() * 1e4),
            "est_corr": float(np.corrcoef(s["est"], s["flow"])[0, 1]),
            "trade": {"mean": float(p.mean()), "t": _t(p), "sr": float(p.mean() / p.std(ddof=1) * math.sqrt(12))},
            "quintiles": [{"est_bp": float(est_bp[g == i].mean()), "mean": float(p[g == i].mean())} for i in range(5)],
            "fade_after": {"mean": float(after.mean()), "t": _t(after)},
            "fix": {"mean": float(f.mean()), "t": _t(f), "sr": float(f.mean() / f.std(ddof=1) * math.sqrt(12))}}


def real():
    with open(DATA / "monthend_summary.csv") as fh:
        return {r["stat"]: r["value"] for r in csv.DictReader(fh)}
