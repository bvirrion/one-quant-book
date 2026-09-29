"""Chart data for One Quant Book 15, chapter 26 (deterministic: cited prices, demand seed 26, sweep seed 13)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from pl_cloudcost import (  # noqa: E402
    PRICES,
    SERVER,
    STORAGE,
    TRANSFER_TIERS,
    C,
    break_evens,
    burst,
    curves,
    demand,
    monthly_to_hourly_rate,
    per_thread,
    plans,
)

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/platforms" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "curves.csv", "w") as f:
    f.write("u,owned,reserved_3y,reserved_1y,on_demand,spot\n")
    for row in curves():
        f.write(",".join(f"{x:.6g}" for x in row) + "\n")
with open(OUT / "break_even.csv", "w") as f:
    f.write("server_factor,owned_per_thread_h,vs_on_demand,vs_spot,reserved_3y_vs_on_demand,server_monthly\n")
    for k in (1, 2, 3):
        b = break_evens(k)
        f.write(f"{k},{b['owned']:.5f},{b['vs_on_demand']:.3f},{b['vs_spot']:.3f},{b['reserved_3y_vs_on_demand']:.3f},"
                f"{C.OwnedServer(**{**SERVER.__dict__, 'price': SERVER.price * k}).monthly:.0f}\n")
d = demand()
with open(OUT / "duration.csv", "w") as f:
    f.write("hours,threads\n")
    s = np.sort(d)[::-1]
    for i in list(range(0, 8760, 20)) + [8759]:
        f.write(f"{i + 1},{s[i]:.0f}\n")
with open(OUT / "plans.csv", "w") as f:
    f.write("plan,owned_threads,reserved_threads,owned,reserved,metered,total\n")
    for name, p in plans(d).items():
        f.write(f"{name},{p.owned},{p.reserved},{p.cost['owned']:.0f},{p.cost['reserved']:.0f},{p.cost['metered']:.0f},"
                f"{p.total:.0f}\n")
with open(OUT / "demand.csv", "w") as f:
    f.write("mean,peak,hours_above_5500\n")
    f.write(f"{d.mean():.0f},{d.max():.0f},{int((d > 5500).sum())}\n")
od = burst(0.0, PRICES["on_demand"].value)
with open(OUT / "burst.csv", "w") as f:
    f.write("rate_per_hour,cost_none,cost_ckpt,makespan_none,makespan_ckpt,wasted_none,wasted_ckpt,on_demand_cost,"
            "on_demand_makespan\n")
    for rate in (0.0, round(monthly_to_hourly_rate(0.2), 6), 0.01, 0.02, 0.05, 0.1, 0.2):
        a, b = burst(rate, PRICES["spot"].value), burst(rate, PRICES["spot"].value, 900.0)
        f.write(f"{rate:g},{a['cost']:.2f},{b['cost']:.2f},{a['makespan_h']:.2f},{b['makespan_h']:.2f},"
                f"{a['wasted_core_h']:.1f},{b['wasted_core_h']:.1f},{od['cost']:.2f},{od['makespan_h']:.2f}\n")
with open(OUT / "data.csv", "w") as f:
    tb = 500
    f.write("tb,transfer_out_usd,storage_usd_month,per_thread_owned,per_thread_on_demand\n")
    p = per_thread()
    f.write(f"{tb},{C.transfer_out(tb * 1024, TRANSFER_TIERS):.0f},{tb * 1024 * STORAGE:.0f},{p['owned']:.5f},"
            f"{p['on_demand']:.6f}\n")
