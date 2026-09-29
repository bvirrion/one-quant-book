"""Chart CSV of chapter 6: maximum clock and latency of a 12-level decision against pipeline depth (model)."""
import nw_fpga as f

OUT = f.ROOT / "figdata" / "networks" / "06-programmable-hardware-i-architecture-and-toolchain"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = ["stages,fmax_mhz,latency_ns"]
    for s in range(1, 7):
        t = f.timing(12, s)
        rows.append(f"{s},{t['fmax_mhz']:.1f},{t['latency_ns']:.2f}")
    (OUT / "pipeline.csv").write_text("\n".join(rows) + "\n")


if __name__ == "__main__":
    main()
