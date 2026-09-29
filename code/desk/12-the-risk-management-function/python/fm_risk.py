"""One Quant Book 16, chapter 12: a year of limit breaches on twenty desks, and who may raise a limit.

Synthetic. Each desk's value at risk against a hard limit of 100 follows a log-AR(1) around 75 per cent utilisation.
When a hard breach opens the desk responds once: it asks for a temporary increase (probability 0.45), changes
its risk model (0.08, measured risk falls by a fifth) or cuts its position (the rest; the log-utilisation then
falls by an extra 0.05 a day). Regime "desk": the head of desk grants increases the next day and model changes
take effect two days later. Regime "committee": both wait for the risk committee, which meets every fifth day
and approves an increase with probability 0.6 (a refused desk cuts); model changes are applied at the meeting.
Regime "committee_cut": as "committee", but a desk that asks for an increase must cut while it waits, and the
request lapses if the breach closes before the meeting.
Temporary increases cover the excess with a margin and expire after 20 days. The register is firm.escalation's.
"""
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/escalation"))
import firm_escalation as fe  # noqa: E402

N_DESKS, N_DAYS, HARD, SOFT = 20, 250, 100.0, 90.0
MU, PHI, SIG = math.log(0.75), 0.98, 0.035

# Public record (ledger F1-F3): the firm-wide risk appetite limit of the examiner's report, $ billion.
LEHMAN_LIMITS = [("2006-11", 2.3), ("2006-12", 3.3), ("2007-09", 3.5), ("2007-12", 4.0)]
LEHMAN_OLD_METHOD_2008 = 2.5


def simulate(regime="desk", seed=12, p_inc=0.45, p_model=0.08, cut=0.05, meet=5, p_approve=0.6, expiry=20,
             n_desks=N_DESKS, n_days=N_DAYS):
    rng = np.random.default_rng(seed)
    y = np.full(n_desks, MU)
    scale = np.ones(n_desks)
    expo = np.zeros((n_desks, n_days))
    hard = np.full((n_desks, n_days), HARD)
    incs = [[] for _ in range(n_desks)]
    models = set()
    state = [None] * n_desks          # None | "cut" | ("inc", day[, cutting]) | ("model", day)

    def next_meeting(t):
        return t + 1 + (-(t + 1)) % meet

    for t in range(n_days):
        eps = rng.standard_normal(n_desks)
        for d in range(n_desks):
            cutting = state[d] == "cut" or (isinstance(state[d], tuple) and len(state[d]) == 3)
            y[d] = MU + PHI * (y[d] - MU) + SIG * eps[d] - (cut if cutting else 0.0)
            st = state[d]
            if isinstance(st, tuple) and st[1] == t:
                if st[0] == "inc":
                    if regime == "desk" or rng.random() < p_approve:
                        need = HARD * math.exp(y[d]) * scale[d] - (HARD + sum(x for x, a, b in incs[d] if a <= t <= b))
                        extra = 5.0 * math.ceil(max(need, 0.0) * 1.5 / 5.0 + 1)
                        incs[d].append((extra, t, t + expiry))
                        state[d] = None
                    else:
                        state[d] = "cut"
                else:
                    scale[d] *= 0.8
                    models.add((d, t))
                    state[d] = None
            lim = HARD + sum(x for x, a, b in incs[d] if a <= t <= b)
            x = HARD * math.exp(y[d]) * scale[d]
            expo[d, t], hard[d, t] = x, lim
            if x <= lim:
                if state[d] == "cut" or (isinstance(state[d], tuple) and len(state[d]) == 3):
                    state[d] = None
            elif state[d] is None:
                u = rng.random()
                if u < p_inc:
                    if regime == "desk":
                        state[d] = ("inc", t + 1)
                    else:
                        state[d] = ("inc", next_meeting(t)) + ((True,) if regime == "committee_cut" else ())
                elif u < p_inc + p_model:
                    state[d] = ("model", t + 2 if regime == "desk" else next_meeting(t))
                else:
                    state[d] = "cut"
    return expo, hard, models


REGIMES = ("desk", "committee", "committee_cut")


def run(regime="desk", seed=12, **kw):
    expo, hard, models = simulate(regime, seed, **kw)
    reg = fe.register(expo, hard, models)
    st = fe.stats(reg)
    st["over_base"] = float(np.mean(expo > HARD))       # share of desk-days above the original hard limit
    return reg, st


def compare(seeds=range(12, 22)):
    """Pooled over ten simulated years: shares by resolution, median and mean days, flagged share."""
    out = {}
    for regime in REGIMES:
        allb, over = [], []
        for s in seeds:
            reg, st = run(regime, s)
            allb += reg
            over.append(st["over_base"])
        st = fe.stats(allb)
        st["over_base"] = float(np.mean(over))
        st["flagged_share"] = st["flagged"] / st["n"]
        st["n_per_year"] = st["n"] / len(list(seeds))
        out[regime] = st
    return out


def model_change_window(seed=12, before=15, after=25):
    """The first breach of the year closed by a model change: its desk, the day of the change, and the window."""
    expo, hard, models = simulate("desk", seed)
    b = next(b for b in fe.register(expo, hard, models) if b.resolution == "model change")
    d, t = b.desk, b.closed
    lo, hi = max(0, t - before), min(expo.shape[1], t + after)
    return d, t, np.arange(lo, hi), expo[d, lo:hi] / HARD, hard[d, lo:hi] / HARD
