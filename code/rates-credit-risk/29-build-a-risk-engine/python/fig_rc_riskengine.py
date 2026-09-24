"""Chart data for Book 6, chapter 29: VaR error by node and method, cost against worst error, and the
short-dated FX desk's P&L under full and approximate revaluation."""
import pathlib

import numpy as np
import rc_riskengine as m
from firm_riskengine import aggregate

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/rates-credit-risk" / HERE.parents[1].name
SHORT = {("Firm",): "Firm", ("Firm", "Rates"): "Rates", ("Firm", "FX"): "FX", ("Firm", "Rates", "Swaps"): "Swaps",
         ("Firm", "Rates", "Options"): "Rate options", ("Firm", "FX", "Short-dated"): "FX short",
         ("Firm", "FX", "Long-dated"): "FX long"}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    e = m.errors(10)
    with open(OUT / "errors_10d.csv", "w") as f:
        f.write("node,grid,dg,plan\n")
        for n, s in SHORT.items():
            f.write(f"{s},{100 * e['grid'][n]['var']:.3f},{100 * e['delta-gamma'][n]['var']:.3f},"
                    f"{100 * e['plan'][n]['var']:.3f}\n")
    with open(OUT / "cost.csv", "w") as f:
        f.write("method,calls,worst1,worst10\n")
        w1, w10 = m.worst(1), m.worst(10)
        calls = {k: v["calls"] for k, v in m.revaluations(10).items()}
        w1["full"] = w10["full"] = 0.0
        for k in ("full", "plan", "grid", "delta-gamma"):
            f.write(f"{k},{calls[k] / 1000:.1f},{100 * w1[k]:.3f},{100 * w10[k]:.3f}\n")
    r = m.revaluations(10)
    paths = [t.path for t in m.book()]
    node = ("Firm", "FX", "Short-dated")
    x = np.array([s.bumps[-1].size for s in m.scenarios(10)])
    cols = {k: aggregate(r[k]["pnl"], paths)[node] for k in ("full", "grid", "delta-gamma")}
    order = np.argsort(x, kind="stable")
    with open(OUT / "fx_short.csv", "w") as f:
        f.write("move,full,grid,dg\n")
        for i in order:
            f.write(f"{100 * x[i]:.4f},{cols['full'][i] / 1e6:.4f},{cols['grid'][i] / 1e6:.4f},"
                    f"{cols['delta-gamma'][i] / 1e6:.4f}\n")


if __name__ == "__main__":
    main()
