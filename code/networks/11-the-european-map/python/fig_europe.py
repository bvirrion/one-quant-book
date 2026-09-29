"""Chart CSVs of chapter 11: the European map and the London inset from computed coordinates, and the
before-and-after floors of Euronext's 2022 migration."""
import nw_europe as e

OUT = e.ROOT / "figdata" / "networks" / "11-the-european-map"

NAMES = {"ld4": "Slough LD4", "fr2": "Frankfurt FR2 (Eurex; Xetra)", "zh4": "Zurich ZH4 (SIX)",
         "bergamo": "Bergamo IT3 (Euronext)", "vasby": "Upplands Vasby (Nasdaq Nordic)",
         "docklands": "Docklands (LSE)", "basildon": "Basildon (ICE; Euronext to 2022)"}
ANCHOR = {"eu": {"ld4": "south", "fr2": "west", "zh4": "east", "bergamo": "west"}}
# link: (from, to, position along the link, label offset x, y in km)
LINKS = {"eu": [("ld4", "fr2", 0.5, 0, 25), ("ld4", "bergamo", 0.3, -95, 0), ("fr2", "bergamo", 0.4, 150, 0)]}
LABELS = {"ld4": "Slough LD4", "docklands": "Docklands", "basildon": "Basildon", "fr2": "FR2", "zh4": "ZH4",
          "bergamo": "Bergamo", "vasby": "Vasby"}


def _t(us):
    return f"{us / 1000:.2f} ms" if us >= 1000 else f"{us:.0f} \\textmu s"


def write_map(region):
    pts = {i: (x, y) for i, x, y in e.map_points(region)}
    rows = ["id,x,y,name,anchor"] + [f"{i},{x:.3f},{y:.3f},{NAMES[i]},{ANCHOR[region][i]}" for i, (x, y) in pts.items()]
    (OUT / f"{region}_sites.csv").write_text("\n".join(rows) + "\n")
    reg = e.registry()
    lines, labels = ["x,y"], ["x,y,text"]
    for a, b, t, dx, dy in LINKS[region]:
        (xa, ya), (xb, yb) = pts[a], pts[b]
        lines += [f"{xa:.3f},{ya:.3f}", f"{xb:.3f},{yb:.3f}", "nan,nan"]
        d = e.distance(a, b, reg)
        x, y = xa + t * (xb - xa) + dx, ya + t * (yb - ya) + dy
        labels.append(f"{x:.3f},{y:.3f},{d / 1e3:.0f} km / {_t(e.gm.floor_us(d))}")
    (OUT / f"{region}_links.csv").write_text("\n".join(lines) + "\n")
    (OUT / f"{region}_labels.csv").write_text("\n".join(labels) + "\n")


def write_migration():
    rows = ["from,vac_before,vac_after,fib_before,fib_after"]
    for r in e.migration():
        rows.append(f"{LABELS[r['from']]},{r['vac_before'] / 1000:.3f},{r['vac_after'] / 1000:.3f},"
                    f"{r['fib_before'] / 1000:.3f},{r['fib_after'] / 1000:.3f}")
    (OUT / "migration.csv").write_text("\n".join(rows) + "\n")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    write_map("eu")
    write_migration()
    rows = ["site,vacuum_ms,fibre_ms"]
    for r in e.nearest_from("ld4"):
        rows.append(f"{LABELS[r['site']]},{r['vacuum_us'] / 1000:.3f},{r['fibre_us'] / 1000:.3f}")
    (OUT / "from_ld4.csv").write_text("\n".join(rows) + "\n")


if __name__ == "__main__":
    main()
