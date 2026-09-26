"""Chapter 14: the compiler's vectorisation report for ll_vecdemo.cpp at -O2, -O3 and -O3 -mavx2 -mfma.

Writes cpp/vecreport/gxx<major>.txt: the "optimized" and "missed" lines of -fopt-info-vec-all (notes dropped), with
the flags in front. Run it again with another g++ to compare versions (GCC 12 and later vectorise at -O2).
"""
import pathlib
import re
import subprocess

HERE = pathlib.Path(__file__).resolve().parents[1]
FLAGS = (("-O2",), ("-O3",), ("-O3", "-mavx2", "-mfma"))


def gxx_major():
    out = subprocess.run(["g++", "-dumpfullversion"], capture_output=True, text=True, check=True).stdout
    return int(out.split(".")[0]), out.strip()


def report(flags):
    cmd = ["g++", "-std=c++20", *flags, "-fopt-info-vec-all", "-I", str(HERE / "cpp"), "-c",
           str(HERE / "cpp/ll_vecdemo.cpp"), "-o", "/dev/null"]
    err = subprocess.run(cmd, capture_output=True, text=True, check=True).stderr
    out = []
    for line in err.splitlines():
        m = re.match(r".*ll_vecdemo\.cpp:(\d+):\d+: (optimized|missed): (.*)", line)
        if m:
            out.append(f"{' '.join(flags):22s}line {m.group(1)}: {m.group(2)}: {' '.join(m.group(3).split())}")
    return out


def lines():
    major, full = gxx_major()
    body = [f"# g++ {full}: vectorisation report for ll_vecdemo.cpp (optimized and missed lines, notes dropped)"]
    for f in FLAGS:
        r = report(f)
        body += r if r else [f"{' '.join(f):22s}(no loop vectorised, nothing reported)"]
    return major, body


def main():
    major, body = lines()
    out = HERE / "cpp/vecreport" / f"gxx{major}.txt"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(body) + "\n")
    print(out)


if __name__ == "__main__":
    main()
