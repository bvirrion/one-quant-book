"""Chapter 22 figure data (deterministic: the engine is): the runaway generator of firm.riskgate against Book 10's
matching engine for five seconds, with each check switched on in turn. Outputs runaway.csv (one row per
configuration: orders sent and refused, shares bought, first refusal, orders sent in the last second, the rate carried
over 45 minutes) and runaway_trace.csv (the position every 50 ms for the configurations of the figure)."""
import csv
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ll_risk as L  # noqa: E402

OUT = L.ROOT / "figdata/low-latency/22-pre-trade-risk-and-kill-switches"
TRACE = ("none", "throttle", "duplicates", "position (in flight)", "capital threshold")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    res = L.runs()
    with open(OUT / "runaway.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["config", "sent", "refused", "position", "first_refusal_ms", "last_second", "shares_45min"])
        for k, s in res.items():
            # still sending at the end: carry the last second's rate over 45 minutes; stopped: where it stopped
            carried = int(L.per_45_minutes(s.last_second * L.ra.CHILD)) if s.last_second else s.position
            w.writerow([k, s.sent, s.refused, s.position, f"{s.first_refusal_ms:.3f}", s.last_second, carried])
    with open(OUT / "runaway_trace.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t_ms", *(k.replace(" (", "_").replace(")", "").replace(" ", "_") for k in TRACE)])
        for i, (t, _) in enumerate(res["none"].trace):
            w.writerow([t, *(res[k].trace[i][1] for k in TRACE)])


if __name__ == "__main__":
    main()
