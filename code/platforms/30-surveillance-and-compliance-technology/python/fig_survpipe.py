"""Chart data for One Quant Book 15, chapter 30 (deterministic: quarter seed 30, calibration seed 31)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from pl_survpipe import FPRS, comms_study, planted_total, queue_study, report_study  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/platforms" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

runs = {(f, p): queue_study(f, p) for f in FPRS for p in ("oldest", "score")}
with open(OUT / "queue.csv", "w") as f:
    f.write("fpr_pct,alerts_per_day,backlog_end,planted_raised,reviewed_oldest,within5_oldest,reviewed_score,"
            "within5_score,median_wait_oldest,planted_total\n")
    total = planted_total()
    for fpr in FPRS:
        a, b = runs[(fpr, "oldest")], runs[(fpr, "score")]
        f.write(f"{100 * fpr:g},{a['alerts_per_day']:.1f},{a['backlog_end']},{a['planted_raised']},"
                f"{a['planted_reviewed']},{a['planted_within_5']},{b['planted_reviewed']},{b['planted_within_5']},"
                f"{a['median_wait']:.0f},{total}\n")
with open(OUT / "backlog.csv", "w") as f:
    f.write("day," + ",".join(f"fpr_{100 * x:g}".replace(".", "p") for x in FPRS) + "\n")
    for d in range(len(runs[(FPRS[0], "oldest")]["backlog"])):
        f.write(f"{d + 1}," + ",".join(str(runs[(x, "oldest")]["backlog"][d]) for x in FPRS) + "\n")
with open(OUT / "comms.csv", "w") as f:
    c = comms_study()
    f.write("messages,conversations,traces,invisible,broad_hits,broad_true,narrow_hits,narrow_true\n")
    f.write(f"{c['messages']},{c['conversations']},{c['planted_traces']},{c['invisible']},{c['broad']['hits']},"
            f"{c['broad']['true_hits']},{c['narrow']['hits']},{c['narrow']['true_hits']}\n")
with open(OUT / "reports.csv", "w") as f:
    r = report_study()
    f.write("kind,legacy,event_sourced,row\n")
    for i, k in enumerate(("invalid", "missing", "extra", "mismatched")):
        f.write(f"{k},{r['legacy'][k]},{r['event-sourced'][k]},{i}\n")
    f.write(f"reports,{r['legacy']['reports']},{r['event-sourced']['reports']},4\n")
