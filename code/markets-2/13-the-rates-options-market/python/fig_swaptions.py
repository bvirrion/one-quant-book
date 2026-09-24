"""Chart data for Book 2, Chapter 13 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from swaption_demo import ATM, EXPIRIES, RATE, annuity, bachelier, black_equivalents, load_negative_yields, smile

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/markets-2/13-the-rates-options-market"
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "payoff.csv", "w") as f:              # 1y x 10y, strike at the 4% forward, per 100 notional
    f.write("s,payer,receiver,payer_value\n")
    a = annuity(1, 11)
    for k in range(0, 41):
        s = 0.02 + k * 0.001
        f.write(f"{100 * s:.1f},{100 * a * max(s - RATE, 0):.4f},{100 * a * max(RATE - s, 0):.4f},"
                f"{100 * bachelier(s, RATE, 1.0, 0.0095, a):.4f}\n")

with open(OUT / "blackequiv.csv", "w") as f:
    f.write("forward,black\n")
    for fw, b in black_equivalents():
        f.write(f"{fw:.2f},{b:.2f}\n")

with open(OUT / "negyields.csv", "w") as f:
    f.write("t,DE,JP\n")
    for d, de, jp in load_negative_yields():
        if "2012-01" <= d < "2023-01":
            f.write(f"{int(d[:4]) + (int(d[5:7]) - 0.5) / 12:.4f},{de:.4f},{jp:.4f}\n")

with open(OUT / "cube.csv", "w") as f:
    f.write("expiry,t2,t10,t30\n")
    for i, e in enumerate(EXPIRIES):
        f.write(f"{e},{ATM[2][i]},{ATM[10][i]},{ATM[30][i]}\n")

with open(OUT / "smile.csv", "w") as f:
    f.write("offset,vol\n")
    for k in range(-8, 9):
        f.write(f"{k * 25},{smile(k * 0.25):.3f}\n")
