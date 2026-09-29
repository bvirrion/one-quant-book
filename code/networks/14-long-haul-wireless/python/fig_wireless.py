"""Chart CSVs of chapter 14: specific rain attenuation by frequency (ITU-R P.838-3), critical rain rate against hop
length, and the route latency through a labelled storm."""
import nw_wireless as w

OUT = w.ROOT / "figdata" / "networks" / "14-long-haul-wireless"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rates = [1, 2, 5, 10, 20, 30, 50, 75, 100, 150]
    rows = ["rain,g6,g11,g18,g80"] + [f"{r}," + ",".join(f"{w.rl.gamma_db_km(r, f):.5f}" for f in (6, 11, 18, 80))
                                      for r in rates]
    (OUT / "gamma.csv").write_text("\n".join(rows) + "\n")
    rows = ["d_km,r6,r11,r18"] + [f"{d},{a:.2f},{b:.2f},{c:.2f}" for d, a, b, c in w.critical_curve()]
    (OUT / "critical.csv").write_text("\n".join(rows) + "\n")
    runs = {p: w.storm(11, p) for p in (50, 100, 150)}
    n = len(runs[50])
    rows = ["minute,p50,p100,p150"] + [f"{m}," + ",".join(f"{runs[p][m][2] / 1000:.3f}" for p in (50, 100, 150))
                                       for m in range(n)]
    (OUT / "storm.csv").write_text("\n".join(rows) + "\n")


if __name__ == "__main__":
    main()
