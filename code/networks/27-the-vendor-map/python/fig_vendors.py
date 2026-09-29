"""Chart CSV of chapter 27: the example firm's yearly spend by vendor (synthetic stack)."""
import nw_vendors as n

OUT = n.ROOT / "figdata" / "networks" / "27-the-vendor-map"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    s = n.report()["shares"]
    rows = ["x,vendor,share"] + [f"{i},{v},{100 * x:.1f}" for i, (v, x) in enumerate(sorted(s.items(),
                                                                                         key=lambda kv: -kv[1]))]
    (OUT / "shares.csv").write_text("\n".join(rows) + "\n")


if __name__ == "__main__":
    main()
