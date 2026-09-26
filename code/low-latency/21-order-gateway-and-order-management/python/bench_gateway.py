"""Chapter 21 measured data (not a fig_*.py): the gateway's cost per call for each step of an order's life, and the
cost of the worst-case exposure check with n open orders, kept as running sums or recomputed by scanning an array or
a hash map. Outputs measured_messages.csv and measured_exposure.csv."""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "code/firm/ubench"))
import firm_ubench as u  # noqa: E402

OUT = ROOT / "figdata/low-latency/21-order-gateway-and-order-management"
SRC = "code/low-latency/21-order-gateway-and-order-management/cpp/ll_gateway_bench.cpp"


def main():
    exe = u.compile_cpp(ROOT / SRC, includes=[ROOT / "code/firm/ordergw/cpp"])
    rows = []
    for line in u.run(exe, "messages", cpus=6).splitlines():
        _, step, q, ns = line.split(",")
        rows.append([step, q, ns])
    u.write_measured(OUT / "measured_messages.csv", ["step", "quantile", "ns"], rows, cpus="6", source=SRC,
                     timer="TSC around each call, median timer cost subtracted", orders="200,000")
    rows = []
    for line in u.run(exe, "exposure", cpus=6).splitlines():
        _, n, sums, arr, hmap = line.split(",")
        rows.append([n, f"{max(0.0, float(sums)):.1f}", arr, hmap])
    u.write_measured(OUT / "measured_exposure.csv", ["open_orders", "sums_ns", "array_ns", "map_ns"], rows, cpus="6",
                     source=SRC, timer="median of TSC-timed calls, timer cost subtracted (clamped at 0)")


if __name__ == "__main__":
    main()
