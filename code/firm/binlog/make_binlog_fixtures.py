"""Write firm.binlog's fixture with the Python reference encoder: data/sample.blog (the statements that the C++ and
Rust tests log, byte for byte) and data/sample.txt (its offline formatting)."""
import pathlib

import firm_binlog as bl

HERE = pathlib.Path(__file__).resolve().parent


def sample():
    w = bl.Writer()
    w.log(1_000, "engine start v{}", "u", 1)
    for k in range(5):
        t = 34_200_000_000_000 + 1_000 * k
        w.log(t, "{} {} at {} x {}", "cciu", "BS"[k % 2], "NR"[k > 1], 999_900 + 100 * k, 100 * (k + 1))
        w.log(t + 10, "fill {} of {} at {}, position {}", "uiii", 40 + k, 100, 999_900 - 100 * k, (k - 2) * 100)
        w.log(t + 20, "{} half-spread {} ticks, skew {}", "sdi", "SIM1", 2.5 + k / 4, -k)
    w.log(34_200_000_009_000, "pulled", "")
    return w


def main():
    w = sample()
    data = w.bytes()
    (HERE / "data/sample.blog").write_bytes(data)
    sites, recs = bl.read(data)
    (HERE / "data/sample.txt").write_text("\n".join(bl.text(sites, recs)) + "\n")


if __name__ == "__main__":
    main()
