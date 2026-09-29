"""Chart data for Book 16, chapter 29 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import fm_cases2 as m  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/desk" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

r = m.race()
with open(OUT / "race.csv", "w") as f:
    f.write("place,m075,m094,m200,needed\n")
    for p in range(1, m.BROKERS + 1):
        f.write(f"{p},{r[0.075][p - 1]:.3f},{r[0.094][p - 1]:.3f},{r[0.2][p - 1]:.3f},"
                f"{100 * m.needed_margin(r['impact'], p):.2f}\n")

k = m.knight()
with open(OUT / "knight.csv", "w") as f:
    f.write("pos,stage,old,new\n")
    f.write(f"0,30 June 2012,{m.cb.KNIGHT['equity_jun_2012']:.1f},0.0\n")
    f.write(f"1,after the loss,{k['after_loss']:.1f},0.0\n")
    f.write(f"2,after the rescue,{k['old_book']:.1f},{k['new_book']:.1f}\n")

x = m.ftx()
with open(OUT / "ftx.csv", "w") as f:
    f.write("day,customers,related\n")
    for d, c, rel in zip(x["date"], x["customers"], x["related"], strict=True):
        f.write(f"{int(d[-2:])},{c / 1000:.3f},{rel / 1000:.3f}\n")

n = m.cb.NICKEL
with open(OUT / "nickel.csv", "w") as f:
    f.write("price,call\n")
    p = n["close_7mar"]
    while p <= n["peak_8mar"] + 1:
        f.write(f"{p / 1000:.3f},{m.cb.margin_call(m.SHORT_T, n['close_7mar'], p) / 1e6:.1f}\n")
        p += (n["peak_8mar"] - n["close_7mar"]) / 20
