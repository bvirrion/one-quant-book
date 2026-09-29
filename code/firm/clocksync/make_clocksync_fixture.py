"""Write data/fixture_servo.csv: a stream of measured offsets through the Python servo (for the C++20 twin)."""
import pathlib

import firm_clocksync as cs
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent


def main():
    rng = np.random.default_rng(5)
    s = cs.Servo()
    rows = ["offset_ns,interval_s,step_ns,freq_ppb"]
    for _ in range(500):
        off = float(rng.normal(0, 2000))
        itv = float(rng.choice([0.125, 1.0, 16.0]))
        step, freq = s.update(off, itv)
        rows.append(f"{off:.9g},{itv},{step:.9g},{freq:.9g}")
    (HERE / "data" / "fixture_servo.csv").write_text("\n".join(rows) + "\n")


if __name__ == "__main__":
    main()
