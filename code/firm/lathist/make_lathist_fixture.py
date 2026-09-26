"""Write the shared fixture of firm.lathist: values (a deterministic mixture spanning 1 ns to 10 s), the expected
non-zero buckets, and the expected quantiles; C++ and Rust tests must reproduce both files exactly."""
import pathlib
import random

from firm_lathist import LatHist

HERE = pathlib.Path(__file__).resolve().parent
PS = (0.0, 0.5, 0.9, 0.99, 0.999, 0.9999, 1.0)


def values(n=20_000, seed=13):
    r = random.Random(seed)
    out = []
    for _ in range(n):
        u = r.random()
        if u < 0.9:
            v = int(r.lognormvariate(6.0, 0.4))            # ~400 ns body
        elif u < 0.999:
            v = int(r.expovariate(1 / 20_000))              # tens of microseconds
        else:
            v = int(r.uniform(1e6, 1e10))                   # stalls up to 10 s
        out.append(v)
    return out


def main():
    vs = values()
    h = LatHist()
    for v in vs:
        h.record(v)
    (HERE / "data/fixture_values.csv").write_text("v\n" + "".join(f"{v}\n" for v in vs))
    (HERE / "data/fixture_buckets.csv").write_text("index,count\n" + "".join(f"{i},{c}\n" for i, c in h.nonzero()))
    (HERE / "data/fixture_quantiles.csv").write_text("p,value\n" + "".join(f"{p},{h.quantile(p)}\n" for p in PS))


if __name__ == "__main__":
    main()
