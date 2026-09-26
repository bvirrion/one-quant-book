"""Chapter 3 of One Quant Book 13: arithmetic on caches and pages (deterministic) and readers of the measured CSVs."""
import csv
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[4]
FIG = ROOT / "figdata/low-latency/03-memory-hierarchy-and-caches"


def rows(name):
    with open(FIG / name, newline="") as f:
        return list(csv.DictReader(f))


def split_address(addr, line=64, sets=64):
    """(tag, set index, offset) of an address in a set-associative cache with `sets` sets of `line`-byte lines."""
    offset = addr % line
    index = (addr // line) % sets
    return addr // (line * sets), index, offset


def cache_geometry(size, line, ways):
    """Number of sets, and the address stride that maps to the same set (the aliasing stride)."""
    sets = size // (line * ways)
    return sets, sets * line


def tlb_reach(entries, page):
    return entries * page


def pages_needed(nbytes, page):
    return -(-nbytes // page)


def books_in(cache_bytes, book_bytes, share=1.0):
    return int(cache_bytes * share // book_bytes)


def stairs():
    return [{k: float(v) for k, v in r.items()} for r in rows("measured_stairs.csv")]


def at(size, key="random_ns"):
    return [r[key] for r in stairs() if int(r["bytes"]) == size][0]
