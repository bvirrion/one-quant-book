"""Chart CSVs of chapter 1: OPRA's published peaks by window; the fan-in simulation (peak rate by window and
drops by egress buffer, with and without market-wide events)."""
import pathlib

import nw_wire as w

OUT = w.ROOT / "figdata" / "networks" / "01-networking-for-trading"
BUFFERS = (10_000, 20_000, 50_000, 100_000, 200_000, 500_000, 1_000_000, 2_000_000, 5_000_000)
WINDOWS_NS = (1_000, 10_000, 100_000, 1_000_000, 10_000_000)


def write(name, header, rows):
    pathlib.Path(OUT).mkdir(parents=True, exist_ok=True)
    lines = [",".join(header)] + [",".join(str(x) for x in r) for r in rows]
    (OUT / name).write_text("\n".join(lines) + "\n")


def main():
    c = w.opra_curve()
    months = sorted(c)
    write("opra.csv", ["window_ms"] + [m.replace("-", "_") for m in months],
          [[c[months[0]][i][0] * 1000] + [round(c[m][i][1], 2) for m in months] for i in range(4)])
    pk = {s: w.peak_by_window(WINDOWS_NS, share=s) for s in (0.0, 0.3)}
    write("peak.csv", ["window_us", "independent", "common"],
          [[x / 1000, round(pk[0.0][i], 2), round(pk[0.3][i], 2)] for i, x in enumerate(WINDOWS_NS)])
    d = {(n, s): w.fanin(BUFFERS, n_feeds=n, share=s) for n in (4, 8) for s in (0.0, 0.3)}
    write("fanin.csv", ["buffer_kb", "f4_independent", "f4_common", "f8_independent", "f8_common"],
          [[b / 1000] + [round(d[k][i], 3) for k in ((4, 0.0), (4, 0.3), (8, 0.0), (8, 0.3))]
           for i, b in enumerate(BUFFERS)])


if __name__ == "__main__":
    main()
