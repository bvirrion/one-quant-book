"""Chart CSV of chapter 28: the recovery-time distributions of the hot and warm designs (labelled simulation)."""
import nw_dr as n

OUT = n.ROOT / "figdata" / "networks" / "28-disaster-recovery-and-regulatory-requirements"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    h = n.rto_hist()
    rows = ["minutes,hot,warm"] + [f"{5 + 10 * i},{a:.4f},{b:.4f}" for i, (a, b) in enumerate(zip(h["hot"], h["warm"],
                                                                                                  strict=True))]
    (OUT / "rto.csv").write_text("\n".join(rows) + "\n")


if __name__ == "__main__":
    main()
