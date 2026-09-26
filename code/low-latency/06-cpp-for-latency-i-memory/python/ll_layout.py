"""Chapter 6 of One Quant Book 13: the x86-64 System V layout of a C++ struct of scalar fields (each aligned to its
size), and readers of the measured CSVs."""
import csv
import pathlib

FIG = pathlib.Path(__file__).resolve().parents[4] / "figdata/low-latency/06-cpp-for-latency-i-memory"
SIZES = {"char": 1, "bool": 1, "int16": 2, "int32": 4, "uint32": 4, "float": 4, "int64": 8, "uint64": 8, "double": 8}


def layout(fields):
    """fields: [(name, type)]. Returns (offsets {name: offset}, size, padding bytes)."""
    off, offsets, align = 0, {}, 1
    for name, t in fields:
        s = SIZES[t]
        off = (off + s - 1) // s * s
        offsets[name] = off
        off += s
        align = max(align, s)
    size = (off + align - 1) // align * align
    return offsets, size, size - sum(SIZES[t] for _, t in fields)


def by_size(fields):
    """The same fields, largest first: the ordering that minimises padding for scalar fields."""
    return sorted(fields, key=lambda f: -SIZES[f[1]])


LOOSE = [("side", "char"), ("price", "double"), ("flag", "char"), ("id", "uint64"), ("qty", "uint32"), ("tif", "char")]


def rows(name):
    with open(FIG / name, newline="") as f:
        return list(csv.DictReader(f))


def fault_cost():
    r = {x["kind"]: (float(x["ns_per_page"]), int(x["faults"])) for x in rows("measured_faults.csv")}
    return r


def churn():
    return {x["allocator"]: {k: float(v) for k, v in x.items() if k != "allocator"} for x in rows("measured_churn.csv")}
