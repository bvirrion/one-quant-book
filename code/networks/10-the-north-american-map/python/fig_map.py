"""Chart CSVs of chapter 10: the two maps (site coordinates, geodesic links and their labels), published routes
against their floors, and the route factors."""
import math

import nw_map as m

OUT = m.ROOT / "figdata" / "networks" / "10-the-north-american-map"

NAMES = {"aurora": "Aurora (CME)", "cermak": "350 Cermak", "markham": "Markham (TMX)", "mahwah": "Mahwah (NYSE)",
         "ny4": "Secaucus: NY4 and NY5 (Cboe)", "carteret": "Carteret (Nasdaq)"}
ANCHOR = {"na": {"aurora": "north", "cermak": "south", "markham": "south", "mahwah": "west", "carteret": "west"},
          "nj": {"mahwah": "south", "ny4": "west", "carteret": "north"}}
LINKS = {"na": [("aurora", "carteret", "vacuum", "ms"), ("markham", "mahwah", "vacuum", "ms")],
         "nj": [("mahwah", "carteret", "vacuum", "us"), ("mahwah", "ny4", "vacuum", "us"),
                ("ny4", "carteret", "vacuum", "us")]}


def _fmt_time(us, unit):
    return f"{us / 1000:.2f} ms" if unit == "ms" else f"{us:.0f} \\textmu s"


def _thin(num):
    """Thousands separated by a thin space, as in the book's text."""
    return num.replace(",", "\\thinspace ")


def write_map(region):
    pts = {i: (x, y) for i, x, y in m.map_points(region)}
    rows = ["id,x,y,name,anchor"] + [f"{i},{x:.3f},{y:.3f},{NAMES[i]},{ANCHOR[region][i]}" for i, (x, y) in pts.items()]
    (OUT / f"{region}_sites.csv").write_text("\n".join(rows) + "\n")
    t = m.sites()
    lines, labels = ["x,y"], ["x,y,text"]
    for a, b, medium, unit in LINKS[region]:
        (xa, ya), (xb, yb) = pts[a], pts[b]
        lines += [f"{xa:.3f},{ya:.3f}", f"{xb:.3f},{yb:.3f}", "nan,nan"]
        d = m.distance(a, b, t)
        us = m.gm.floor_us(d, medium)
        labels.append(f"{(xa + xb) / 2:.3f},{(ya + yb) / 2:.3f},{_thin(f'{d / 1e3:,.1f}')} km / {_fmt_time(us, unit)}")
    (OUT / f"{region}_links.csv").write_text("\n".join(lines) + "\n")
    (OUT / f"{region}_labels.csv").write_text("\n".join(labels) + "\n")


def write_routes():
    rows = ["label,medium,km,published_ms,floor_ms,factor,excess_us"]
    for r in m.route_rows():
        rows.append(f"{r['label']},{r['medium']},{r['km']:.2f},{r['published_us'] / 1000:.3f},"
                    f"{r['floor_us'] / 1000:.3f},{r['factor']:.4f},{r['excess_us']:.1f}")
    (OUT / "routes.csv").write_text("\n".join(rows) + "\n")
    for medium in ("air", "fibre"):
        sub = [rows[0]] + [r for r in rows[1:] if r.split(",")[1] == medium]
        (OUT / f"routes_{medium}.csv").write_text("\n".join(sub) + "\n")
    floors = ["km,vacuum_ms,fibre_ms"]
    for km in (0, 1250):
        d = km * 1e3
        floors.append(f"{km},{m.gm.floor_us(d, 'vacuum') / 1000:.4f},{m.gm.floor_us(d, 'fibre') / 1000:.4f}")
    (OUT / "floors.csv").write_text("\n".join(floors) + "\n")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for region in ("na", "nj"):
        write_map(region)
    write_routes()
    assert not any(math.isnan(r["factor"]) for r in m.route_rows())


if __name__ == "__main__":
    main()
