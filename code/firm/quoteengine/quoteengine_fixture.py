"""Writes data/fixture_events.csv (a scripted stream of target updates, acknowledgements and fills) and
data/fixture_expected.csv (the Python engine's actions), replayed by cpp/ and rust/."""
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import firm_quoteengine as qe  # noqa: E402

PARAMS = {"min_move": 2, "min_size": 100, "rate": 20.0, "burst": 5.0}


def script(n: int = 3000, seed: int = 7):
    """Events drawn while running an engine, so that acknowledgements and fills name orders that exist."""
    rng = np.random.default_rng(seed)
    e = qe.QuoteEngine(**PARAMS)
    mid, t, rows = 1000, 0.0, []
    for step in range(n):
        t += float(rng.exponential(0.02))
        u = rng.random()
        pending = sorted(o.oid for o in e.orders.values() if o.state != "live")
        live = sorted(o.oid for o in e.orders.values() if o.state in ("live", "pending_cancel"))
        if u < 0.5 or (not pending and not live):
            mid += int(rng.integers(-1, 2))
            side = 1 if rng.random() < 0.5 else -1
            levels = int(rng.integers(0, 4))
            targets = [(mid - side * (1 + k), int(100 * rng.integers(1, 4))) for k in range(levels)]
            e.update(t, side, targets)
            rows.append((step, "U", t, side, "|".join(f"{p}:{q}" for p, q in targets), 0, 0))
        elif (u < 0.85 and pending) or not live:
            oid = int(rng.choice(pending))
            e.ack(oid)
            rows.append((step, "A", t, 0, "", oid, 0))
        else:
            oid = int(rng.choice(live))
            q = int(100 * rng.integers(1, 3))
            e.fill(oid, q)
            rows.append((step, "F", t, 0, "", oid, q))
    return rows


def replay(rows):
    e = qe.QuoteEngine(**PARAMS)
    out = []
    for step, kind, t, side, tg, oid, qty in rows:
        if kind == "U":
            targets = [tuple(int(x) for x in s.split(":")) for s in tg.split("|")] if tg else []
            for a in e.update(t, side, targets):
                out.append((step, " ".join(str(x) for x in a)))
        elif kind == "A":
            e.ack(oid)
        else:
            e.fill(oid, qty)
    return out, e.stats


if __name__ == "__main__":
    rows = script()
    acts, stats = replay(rows)
    d = HERE / "data"
    (d / "fixture_params.csv").write_text("min_move,min_size,rate,burst\n" + ",".join(repr(PARAMS[k]) for k in PARAMS)
                                          + "\n")
    (d / "fixture_events.csv").write_text("step,kind,t,side,targets,oid,qty\n" + "".join(
        f"{s},{k},{t!r},{sd},{tg},{o},{q}\n" for s, k, t, sd, tg, o, q in rows))
    (d / "fixture_expected.csv").write_text("step,action\n" + "".join(f"{s},{a}\n" for s, a in acts))
    print(len(rows), "events", len(acts), "actions", stats)
