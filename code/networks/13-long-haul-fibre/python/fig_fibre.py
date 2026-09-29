"""Chart CSVs of chapter 13: latency components of the 2010 Chicago-New Jersey route rebuilt four ways, the implied
path factor against the assumed equipment time, and illustrative dark-against-lit cumulative costs."""
import nw_fibre as n

OUT = n.ROOT / "figdata" / "networks" / "13-long-haul-fibre"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = ["variant,glass,path,dcf,equipment"]
    for k, c in n.variants().items():
        rows.append(f"{k},{c['glass'] / 1e3:.4f},{max(c['path'], 0) / 1e3:.4f},{c['dcf'] / 1e3:.4f},"
                    f"{(c['amps'] + c['terminals']) / 1e3:.4f}")
    (OUT / "components.csv").write_text("\n".join(rows) + "\n")
    (OUT / "sensitivity.csv").write_text("equipment_us,factor\n" + "".join(f"{e},{f:.5f}\n" for e, f in
                                                                          n.sensitivity(range(0, 201, 10))))
    (OUT / "costs.csv").write_text("year,dark_m,lit_m\n" + "".join(f"{y},{d / 1e6:.3f},{v / 1e6:.3f}\n"
                                                                 for y, d, v in n.costs()))


if __name__ == "__main__":
    main()
