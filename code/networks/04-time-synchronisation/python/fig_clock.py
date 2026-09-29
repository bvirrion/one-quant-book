"""Chart CSVs of chapter 4: offset envelopes of four disciplining set-ups (first ten minutes, largest |offset| in
each 5-second window) and the Allan deviation of the free-running and disciplined clocks. Simulation."""
import numpy as np
import nw_clock as c

OUT = c.ROOT / "figdata" / "networks" / "04-time-synchronisation"
KEYS = {"software": "sw", "hardware": "hw", "hardware, min-delay filter": "hw_filter",
        "hardware, transparent clocks": "hw_tc"}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    env = {}
    for name, k in KEYS.items():
        r = c.run(name, hours=600 / 3600)
        o = np.abs(r["offset_ns"]).reshape(-1, 40).max(axis=1)          # 40 exchanges of 0.125 s = 5 s
        env[k] = np.maximum(o, 1.0)
    t = (np.arange(len(env["sw"])) + 1) * 5
    rows = ["t_s," + ",".join(env)] + [f"{t[i]}," + ",".join(f"{env[k][i]:.1f}" for k in env) for i in range(len(t))]
    (OUT / "offset.csv").write_text("\n".join(rows) + "\n")
    free, disc = c.adev()
    rows = ["tau_s,free,disciplined"] + [f"{a[0]},{a[1]:.4e},{b[1]:.4e}" for a, b in zip(free, disc, strict=True)]
    (OUT / "adev.csv").write_text("\n".join(rows) + "\n")


if __name__ == "__main__":
    main()
