"""Chart CSVs of chapter 18: simulated round trips by path, and monthly cost against message volume."""
import nw_private as n

OUT = n.ROOT / "figdata" / "networks" / "18-private-connectivity-to-crypto-venues"
SHORT = {"peering_cpg": "peering + shared cluster", "peering": "peering", "endpoint_same": "endpoint same zone",
         "endpoint_other": "endpoint other zone", "internet": "public via edge"}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = ["path,p50,p99"] + [f"{SHORT[r['key']]},{r['p50']:.1f},{r['p99']:.1f}" for r in n.path_rows()]
    (OUT / "paths.csv").write_text("\n".join(rows) + "\n")
    rows = ["millions,same,other"] + [f"{v},{a:.3f},{b:.3f}" for v, a, b in n.monthly_curve()]
    (OUT / "monthly.csv").write_text("\n".join(rows) + "\n")


if __name__ == "__main__":
    main()
