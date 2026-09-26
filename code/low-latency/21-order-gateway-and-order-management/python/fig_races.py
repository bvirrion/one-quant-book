"""Chapter 21 figure data (deterministic: the engine and the seeds are): the fraction of cancels that met a fill, for
one-way latencies from 10 us to 3 ms, from firm.ordergw's runs against Book 10's matching engine (fills at 200 a
second, orders held 1 ms on average), with the exact race probability and the formula for orders that rested at
least L + d. Outputs races.csv and race_curves.csv."""
import csv
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ll_gateway as L  # noqa: E402

OUT = L.ROOT / "figdata/low-latency/21-order-gateway-and-order-management"
LAT_US = (10, 30, 100, 300, 1000, 3000)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "races.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["latency_us", "races", "cancels", "simulated", "exact", "rested"])
        for us in LAT_US:
            races, cancels = L.simulate(us * 1000)
            w.writerow([us, races, cancels, f"{races / cancels:.4f}", f"{L.race_exact(L.LAM, us * 1e-6, L.HOLD):.4f}",
                        f"{L.race_rested(L.LAM, us * 1e-6):.4f}"])
    # the smooth curves, on a finer grid
    with open(OUT / "race_curves.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["latency_us", "exact", "rested"])
        for k in range(41):
            us = 10 ** (1 + 2.6 * k / 40)
            w.writerow([f"{us:.2f}", f"{L.race_exact(L.LAM, us * 1e-6, L.HOLD):.5f}",
                        f"{L.race_rested(L.LAM, us * 1e-6):.5f}"])


if __name__ == "__main__":
    main()
