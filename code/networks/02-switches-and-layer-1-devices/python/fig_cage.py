"""Chart CSVs of chapter 2: latency added by each device against frame size; multiplexer contention (simulation)."""
import pathlib

import nw_cage as c

OUT = c.ROOT / "figdata" / "networks" / "02-switches-and-layer-1-devices"
JITTERS = (25, 50, 100, 200, 400, 800, 1600)


def write(name, header, rows):
    pathlib.Path(OUT).mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text("\n".join([",".join(header)] + [",".join(str(x) for x in r) for r in rows]) + "\n")


def main():
    write("forwarding.csv", ["frame", "store_forward", "cut_through", "mux", "l1"],
          [[f] + [round(x, 1) for x in r] for f, *r in c.forwarding_curve()])
    rows = []
    for j in JITTERS:
        rows.append([j] + [round(c.mux_contention(k, j)["mean"], 1) for k in (2, 4, 8)])
    write("mux.csv", ["jitter_ns", "k2", "k4", "k8"], rows)


if __name__ == "__main__":
    main()
