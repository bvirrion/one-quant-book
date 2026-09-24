"""Chart data for Chapter 7 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from pnl_day import CLOSING_MID, FILLS, U, explain, three_numbers, units

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/pnl"))
from firm_pnl import Position

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/markets-1/07-pnl-and-positions"
OUT.mkdir(parents=True, exist_ok=True)

p = Position()
with open(OUT / "day.csv", "w") as f:
    f.write("k,time,position_k,realised_k,unrealised_k,total_k\n")
    f.write("0,09:30,0,0,0,0\n")
    for k, (t, side, qty, price, mid) in enumerate(FILLS, start=1):
        p.on_fill(side, qty, units(price))
        m = units(mid)
        f.write(f"{k},{t},{p.quantity / 1000:.0f},{p.realised / U / 1000:.3f},"
                f"{p.unrealised(m) / U / 1000:.3f},{p.total(m) / U / 1000:.3f}\n")
    m = units(CLOSING_MID)
    f.write(f"7,16:00,{p.quantity / 1000:.0f},{p.realised / U / 1000:.3f},"
            f"{p.unrealised(m) / U / 1000:.3f},{p.total(m) / U / 1000:.3f}\n")

n = three_numbers()
with open(OUT / "three_numbers.csv", "w") as f:
    f.write("k,label,usd_k\n")
    rows = [("Trader (last print; gross)", n["trader"]), ("Risk (closing mid; gross)", n["risk"]),
            ("Finance (official close; net)", n["finance"])]
    f.writelines(f"{i},{lab},{v / 1000:.1f}\n" for i, (lab, v) in enumerate(rows))

day2 = [("10:00", -1, 10_000, 50.35, 0.0), ("14:00", 1, 5_000, 50.10, 0.0)]
e = explain(30_000, 50.00, 50.40, day2, 900.0, 650.0)
with open(OUT / "explain.csv", "w") as f:
    f.write("k,label,usd_k\n")
    f.writelines(f"{i},{k},{v / 1000:.2f}\n" for i, (k, v) in enumerate(e.items()))
