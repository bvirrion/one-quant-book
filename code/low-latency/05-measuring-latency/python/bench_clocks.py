"""Chapter 5 measured data (not a fig_*.py): cost per call of each clock, and ten TSC calibrations (CPU 2)."""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/ubench"))
import firm_ubench as u  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "figdata/low-latency/05-measuring-latency"
SRC = "code/low-latency/05-measuring-latency/cpp/ll_clocks_bench.cpp"


def main():
    exe = u.compile_cpp(HERE / "cpp/ll_clocks_bench.cpp")
    clocksource = pathlib.Path("/sys/devices/system/clocksource/clocksource0/current_clocksource")
    cs = clocksource.read_text().strip() if clocksource.exists() else "unknown"
    for mode, name in (("costs", "measured_clocks.csv"), ("calib", "measured_tsc.csv")):
        lines = u.run(exe, mode, cpus="2").strip().splitlines()
        u.write_measured(OUT / name, lines[0].split(","), [x.split(",") for x in lines[1:]], flags=" ".join(u.DEFAULT),
                         cpus="2", clocksource=cs, source=SRC)


if __name__ == "__main__":
    main()
