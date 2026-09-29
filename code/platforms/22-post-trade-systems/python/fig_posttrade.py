"""Chart data for One Quant Book 15, chapter 22 (deterministic: a synthetic week of trades and confirms, seed 22)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from pl_posttrade import RATES, breaks, confirms, custodian_recon, match_rates, trades, week  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/platforms" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "match_rate.csv", "w") as f:
    f.write("tolerance,rate_pct,partial,ours_only,theirs_only\n")
    for tol, rate, part, o, t in match_rates(tols=(1e-7, 1e-6, 1e-5, 5e-5, 1e-4, 1e-3, 1e-2, 5e-2)):
        f.write(f"{tol:g},{100 * rate:.1f},{part},{o},{t}\n")
with open(OUT / "cycles.csv", "w") as f:
    f.write("cycle,breaks,fixed,failed,failed_value_m,recon_breaks,age_lt1,age_1_3,age_3_7\n")
    for c in ("T+2", "T+1"):
        w, r = week(c), custodian_recon(c)
        a = r["ageing"]
        f.write(f"{c},{w['breaks']},{w['breaks'] - w['failed']},{w['failed']},{w['failed_value'] / 1e6:.2f},"
                f"{r['breaks']},{a['under 1 day']},{a['1 to 3 days']},{a['3 to 7 days']}\n")
with open(OUT / "staffing.csv", "w") as f:
    f.write("staff,failed,failed_value_m,failed_half_errors,failed_value_half_m\n")
    half = dict(RATES, account=RATES["account"] / 2, missing=RATES["missing"] / 2)
    for s in range(3, 9):
        a, b = week("T+1", staff=s), week("T+1", staff=s, rates=half)
        f.write(f"{s},{a['failed']},{a['failed_value'] / 1e6:.2f},{b['failed']},{b['failed_value'] / 1e6:.2f}\n")
with open(OUT / "kinds.csv", "w") as f:
    f.write("kind,breaks,failed_t2,failed_t1\n")
    w2, w1, tot = week("T+2"), week("T+1"), {}
    for d in range(5):
        o = trades(d, 1)
        for b in breaks(o, confirms(o, seed=22 + d)[0]):
            tot[b["kind"]] = tot.get(b["kind"], 0) + 1
    for k in ("account", "missing", "settle_date", "price", "qty"):
        f.write(f"{k},{tot[k]},{w2['by_kind'].get(k, 0)},{w1['by_kind'].get(k, 0)}\n")
