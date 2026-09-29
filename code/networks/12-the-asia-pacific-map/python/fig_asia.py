"""Chart CSVs of chapter 12: the Asia-Pacific map, receive delay by login rank (unicast), and the sorted receive
delays of the four dissemination designs (a labelled simulation)."""
import numpy as np
import nw_asia as a

OUT = a.ROOT / "figdata" / "networks" / "12-the-asia-pacific-map"
NAMES = {"tokyo": "Tokyo (JPX)", "tko": "Hong Kong TKO (HKEX)", "singapore": "Singapore (SGX)",
         "alc": "Sydney ALC (ASX)", "bkc": "Mumbai BKC (NSE)"}
ANCHOR = {"tokyo": "south", "tko": "south west", "singapore": "north", "alc": "east", "bkc": "south"}
# link: (from, to, label offset x, y in km from the midpoint, so that no label sits on a line or a name)
LINKS = [("tokyo", "tko", -700, 350), ("tko", "singapore", 1100, 0), ("singapore", "alc", -1300, -250),
         ("singapore", "bkc", 0, -450)]


def _thin(num):
    """Thousands separated by a thin space, as in the book's text."""
    return num.replace(",", "\\thinspace ")


def write_map():
    pts = {i: (x, y) for i, x, y in a.map_points()}
    rows = ["id,x,y,name,anchor"] + [f"{i},{x:.1f},{y:.1f},{NAMES[i]},{ANCHOR[i]}" for i, (x, y) in pts.items()]
    (OUT / "map_sites.csv").write_text("\n".join(rows) + "\n")
    t = a.sites()
    lines, labels = ["x,y"], ["x,y,text"]
    for p, q, dx, dy in LINKS:
        (xa, ya), (xb, yb) = pts[p], pts[q]
        lines += [f"{xa:.1f},{ya:.1f}", f"{xb:.1f},{yb:.1f}", "nan,nan"]
        d = a.gm.geodesic_m(t[p].lat, t[p].lon, t[q].lat, t[q].lon)
        km = _thin(f"{d / 1e3:,.0f}")
        labels.append(f"{(xa + xb) / 2 + dx:.1f},{(ya + yb) / 2 + dy:.1f},{km} km / {a.gm.floor_us(d) / 1e3:.1f} ms")
    (OUT / "map_links.csv").write_text("\n".join(lines) + "\n")
    (OUT / "map_labels.csv").write_text("\n".join(labels) + "\n")


def write_rank_curve():
    rc = a.rank_curve()
    servers = [s.name for s in a.TOPOLOGY if s.name != "secondary"]
    rows = ["rank," + ",".join(f"s{k + 1}" for k in range(len(servers)))]
    for r in range(10):
        rows.append(f"{r + 1}," + ",".join(f"{rc[(s, r)]:.2f}" for s in servers))
    (OUT / "rank_curve.csv").write_text("\n".join(rows) + "\n")


def write_sorted():
    cols = {}
    for name, kind, shuffle, topo in a.DESIGNS:
        if name == "unicast, randomised":
            continue
        t = a._tick(kind, shuffle, np.random.default_rng(1), topo)
        v = sorted(float(x) for x in t.values())
        cols[name] = [100 * k / (len(v) - 1) for k in range(len(v))], v
    for name, (pct, v) in cols.items():
        slug = {"unicast": "unicast", "unicast, randomised, no secondary": "randomised", "multicast": "multicast"}[name]
        rows = ["pct,us"] + [f"{p:.2f},{x:.2f}" for p, x in zip(pct, v, strict=True)]
        (OUT / f"sorted_{slug}.csv").write_text("\n".join(rows) + "\n")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    write_map()
    write_rank_curve()
    write_sorted()


if __name__ == "__main__":
    main()
