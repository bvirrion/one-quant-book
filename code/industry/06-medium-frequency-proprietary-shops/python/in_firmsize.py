"""One Quant Book 17, chapter 6: how large proprietary trading firms are, from FINRA's published counts.

FINRA counts broker-dealers by the number of registered representatives (people registered to deal with the public),
not by staff; the proprietary-trading and market-making segments are counted separately (chapter 1). The chapter fits
a Pareto tail to the size bins with firm.firmsize and reads entry and exit.
"""
import csv
import functools
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/firmsize"))
import firm_firmsize as fs  # noqa: E402

DATA = ROOT / "data/industry"
X_MIN = 11


def bins(year=2024):
    with open(DATA / "finra_size_bins.csv") as f:
        return [fs.Bin(int(r["lo"]), int(r["hi"]) if r["hi"] else None, int(r[f"y{year}"])) for r in csv.DictReader(f)]


@functools.cache
def fit(year=2024, x_min=X_MIN):
    b = bins(year)
    p, ln = fs.pareto_fit(b, x_min), fs.lognormal_fit(b, x_min)
    return dict(pareto=p, lognormal=ln, chi2_pareto=fs.chi2(b, fs.expected_counts(b, x_min, p)),
                chi2_lognormal=fs.chi2(b, fs.expected_counts(b, x_min, ln)), bins_used=sum(x.lo >= x_min for x in b))


def shares(year=2024):
    b = bins(year)
    tot = sum(x.n for x in b)
    with open(DATA / "finra_reps_by_size.csv") as f:
        reps = {int(r["year"]): {k: int(v) for k, v in r.items() if k != "year"} for r in csv.DictReader(f)}[year]
    return dict(firms=tot, le10=b[0].n / tot, le50=sum(x.n for x in b if x.hi and x.hi <= 50) / tot,
                small_reps=reps["small"] / sum(reps.values()), large_reps=reps["large"] / sum(reps.values()),
                reps=sum(reps.values()))


def entry_exit():
    with open(DATA / "finra_entry_exit.csv") as f:
        rows = [{k: int(v) for k, v in r.items()} for r in csv.DictReader(f)]
    for prev, cur in zip(rows[:-1], rows[1:], strict=True):
        cur["exit_rate"] = cur["leaving"] / prev["total_end"]
        cur["entry_rate"] = cur["entering"] / prev["total_end"]
    return rows[1:]
