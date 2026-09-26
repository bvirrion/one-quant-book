"""Chart data for Book 12, chapter 23: training loss in float32 and under bfloat16 autocast (smoothed over 10 steps)."""
import pathlib

import ml_train as m
import numpy as np

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata" / "ml" / "23-training-infrastructure"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    _, l32 = m.run(bf16=False)
    _, l16 = m.run(bf16=True)
    k = np.ones(10) / 10
    a, b = np.convolve(l32, k, "valid"), np.convolve(l16, k, "valid")
    with open(OUT / "losses.csv", "w") as f:
        f.write("step,fp32,bf16\n")
        for i in range(0, len(a), 5):
            f.write(f"{i + 10},{a[i]:.5f},{b[i]:.5f}\n")


if __name__ == "__main__":
    main()
