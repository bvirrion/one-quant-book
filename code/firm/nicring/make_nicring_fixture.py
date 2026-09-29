"""Write data/events.txt and data/expected.txt (firm.nicring's shared fixture): one event stream, four ring
configurations, the Python reference's counters and hash for each."""
import pathlib

import firm_nicring as nr

HERE = pathlib.Path(__file__).resolve().parent
CONFIGS = ((64, 1), (64, 16), (16, 8), (256, 32))


def main():
    ev = nr.make_events(20_000, 3.0, 4, seed=11)
    (HERE / "data" / "events.txt").write_text("\n".join(" ".join(str(x) for x in e) for e in ev) + "\n")
    lines = ["# size refill rx drops processed doorbells max_owned hash"]
    for size, refill in CONFIGS:
        r = nr.Ring(size, refill).run(ev)
        lines.append(f"{size} {refill} {r.rx} {r.drops} {r.processed} {r.doorbells} {r.max_owned} {r.hash:016x}")
    (HERE / "data" / "expected.txt").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
