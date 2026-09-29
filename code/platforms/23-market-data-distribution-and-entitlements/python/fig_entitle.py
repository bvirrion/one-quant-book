"""Chart data for One Quant Book 15, chapter 23 (deterministic: tapes seeded 2300-2319, usage log seed 23)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from pl_entitle import MONTHS, REVOKE_AT, audit, distribute, non_display_fee, updates  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/platforms" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

ups = updates()
runs = {"all": distribute(ups, "all", trace_every=2000), "conflate": distribute(ups, "conflate", trace_every=500)}
with open(OUT / "distribution.csv", "w") as f:
    f.write("policy,subscriber,delivered,max_depth,mean_age_ms,max_age_ms,denied\n")
    for pol, r in runs.items():
        for name, s in r.items():
            f.write(f"{pol},{name},{s.delivered},{s.max_depth},{1e3 * s.mean_age:.1f},{1e3 * s.max_age:.1f},"
                    f"{s.denied}\n")
for pol, r in runs.items():
    with open(OUT / f"age_{pol}.csv", "w") as f:
        f.write("t,age_s\n")
        for t, a in r["research"].trace:
            f.write(f"{t:.1f},{a:.3f}\n")
nocheck = distribute(ups, "conflate", check_on_delivery=False)["screen"]
with open(OUT / "revocation.csv", "w") as f:
    f.write("check,delivered,after_revocation\n")
    s = runs["conflate"]["screen"]
    f.write(f"every delivery,{s.delivered},0\nsubscribe only,{nocheck.delivered},{nocheck.delivered - s.delivered}\n")
a = audit()
with open(OUT / "usage.csv", "w") as f:
    f.write("month,display_used,display_licensed,nd_used,nd_licensed,owed\n")
    for r in a["rows"]:
        f.write(f"{r.month},{r.used['display']},{r.licensed['display']},{r.used['non-display']},"
                f"{r.licensed['non-display']},{r.owed:.2f}\n")
with open(OUT / "audit.csv", "w") as f:
    f.write("months,owed,display_owed,non_display_owed,under_pct,revoke_at\n")
    f.write(f"{MONTHS},{a['owed']:.2f},{a['display_owed']:.2f},{a['non_display_owed']:.2f},{a['under_pct']:.1f},"
            f"{REVOKE_AT:g}\n")
with open(OUT / "fees.csv", "w") as f:
    f.write("devices,fee\n")
    for n in range(0, 121):
        f.write(f"{n},{non_display_fee(n):.2f}\n")
