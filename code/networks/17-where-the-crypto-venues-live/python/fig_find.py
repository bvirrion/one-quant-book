"""Chart CSVs of chapter 17: the triangulation example, the instance lottery and its net value, and a venue move
flagged by the CUSUM test (labelled simulations)."""
import numpy as np
import nw_find as f

OUT = f.ROOT / "figdata" / "networks" / "17-where-the-crypto-venues-live"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    t = f.triangulate_example()
    pts = [(s, f.SITES[s].lat, f.SITES[s].lon) for s in f.PROBE_SITES]
    pts += [("server (hidden)", *f.TRUE), ("estimate", *t["estimate"])]
    xy = f.gm.project([f.gm.Site(n, n, "", la, lo, "") for n, la, lo in pts], 15.0, 120.0)
    names = {"tko": "Hong Kong probe", "singapore": "Singapore probe", "alc": "Sydney probe", "bkc": "Mumbai probe"}
    rows = ["x,y,name,kind"] + [f"{xy[n][0]:.1f},{xy[n][1]:.1f},{names.get(n, n)},{'probe' if n in names else n}"
                                for n, _, _ in pts]
    (OUT / "triangulation.csv").write_text("\n".join(rows) + "\n")
    rows = ["n,best_us"] + [f"{n},{v:.2f}" for n, v in f.lottery_curve(tuple(range(1, 11)) + (15, 20, 30, 40, 60, 80,
                                                                                            100, 130, 160))]
    (OUT / "lottery.csv").write_text("\n".join(rows) + "\n")
    base = f.vf.expected_best(f.LOTTERY, 1, 4000, 0)
    rows = ["n,net_k"]
    for n in (1, 5, 10, 20, 40, 60, 77, 100, 120, 150):
        net = f.VALUE * (base - f.vf.expected_best(f.LOTTERY, n, 4000, 0)) - f.LAUNCH * n
        rows.append(f"{n},{net / 1000:.3f}")
    (OUT / "net.csv").write_text("\n".join(rows) + "\n")
    x, day = f.drift_example()
    rows = ["day,median_us,flag"] + [f"{k + 1},{v:.2f},{int(k == day + 1)}" for k, v in enumerate(np.asarray(x))]
    (OUT / "drift.csv").write_text("\n".join(rows) + "\n")


if __name__ == "__main__":
    main()
