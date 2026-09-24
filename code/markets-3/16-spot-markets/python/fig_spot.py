"""Chart data for Book 3, Chapter 16 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from m3_spot import BENFORD, first_digits, genuine_tape, mixed_tape, p_loss

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/markets-3" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "latency.csv", "w") as f:
    f.write("minutes,g50,g100,g200\n")
    for t in range(1, 61):
        f.write(f"{t}," + ",".join(f"{100 * p_loss(g, 20, t, 0.6):.2f}" for g in (50, 100, 200)) + "\n")

g, x = genuine_tape(20_000), mixed_tape(20_000, 0.7)
with open(OUT / "digits.csv", "w") as f:
    f.write("digit,benford,genuine,mixed\n")
    for d, (b, u, v) in enumerate(zip(BENFORD, first_digits(g), first_digits(x), strict=True), 1):
        f.write(f"{d},{100 * b:.2f},{100 * u:.2f},{100 * v:.2f}\n")

with open(OUT / "sizes.csv", "w") as f:
    f.write("size,genuine,mixed\n")
    for k in range(50):
        lo, hi = 10 * k, 10 * (k + 1)
        cg = sum(lo <= s < hi for s in g) / len(g)
        cx = sum(lo <= s < hi for s in x) / len(x)
        f.write(f"{lo / 10_000:.3f},{100 * cg:.2f},{100 * cx:.2f}\n")
