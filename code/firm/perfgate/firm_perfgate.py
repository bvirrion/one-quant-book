"""firm.perfgate -- performance regression gate, certification runner and deployment preflight (build of One Quant
Book 13, chapter 25). Python.

A performance gate compares a candidate build (B) with the current one (A) on the same machine, interleaving their runs
(A B B A ...) so that slow drifts of the machine hit both alike, and decides from the per-run statistics (a percentile
of latency per run) whether B is slower by more than a tolerance. A shared, noisy machine makes single runs useless;
the gate's answer is only as good as its number of runs, which power() estimates from the machine's measured noise.

API (stable):
    interleave(n_pairs) -> ["A", "B", "B", "A", ...]           the ABBA order of runs
    run_pairs(cmd_a, cmd_b, n_pairs, parse) -> (a_stats, b_stats)   runs two commands (lists) in that order
    compare(a, b, tolerance=0.02, alpha=0.05, n_perm=2000, n_boot=2000, seed=0) -> Verdict
        rise = median(b) / median(a) - 1; one-sided permutation p-value on the difference of medians; bootstrap
        interval of the rise; regression = p < alpha and rise > tolerance
    power(a_pool, b_pool, n, trials=200, shift=0, **kw) -> fraction of gates on n runs each that flag B
    runs_needed(cv, rise, alpha=0.05, beta=0.10) -> runs per side for that power (normal approximation)
    certify(script, engine=None) -> [(step, ok, got)]         runs a certification script against Book 10's engine
    preflight(root, plan) -> (ok, findings)                   firm.tuneaudit on the host before a deployment
"""
import json
import pathlib
import random
import statistics
import subprocess
import sys
from dataclasses import dataclass

HERE = pathlib.Path(__file__).resolve().parent
for c in ("exchsim", "tape", "tuneaudit", "coreplan"):
    sys.path.insert(0, str(HERE.parent / c))


def interleave(n_pairs):
    out = []
    for i in range(n_pairs):
        out += ["A", "B"] if i % 2 == 0 else ["B", "A"]
    return out


def run_pairs(cmd_a, cmd_b, n_pairs, parse=float):
    a, b = [], []
    for v in interleave(n_pairs):
        res = subprocess.run(cmd_a if v == "A" else cmd_b, capture_output=True, text=True, check=True)
        (a if v == "A" else b).append(parse(res.stdout))
    return a, b


@dataclass
class Verdict:
    rise: float
    p_value: float
    low: float
    high: float
    regression: bool

    def report(self):
        word = "REGRESSION" if self.regression else "ok"
        return (f"{word}: p99 {self.rise:+.1%} (90% interval {self.low:+.1%} to {self.high:+.1%}), "
                f"permutation p = {self.p_value:.3f}")


def compare(a, b, tolerance=0.02, alpha=0.05, n_perm=2000, n_boot=2000, seed=0):
    rng = random.Random(seed)
    ma, mb = statistics.median(a), statistics.median(b)
    rise = mb / ma - 1
    observed = mb - ma
    pooled, na = list(a) + list(b), len(a)
    hits = 0
    for _ in range(n_perm):
        rng.shuffle(pooled)
        if statistics.median(pooled[na:]) - statistics.median(pooled[:na]) >= observed:
            hits += 1
    p = (hits + 1) / (n_perm + 1)
    low = high = float("nan")
    if n_boot:
        boots = []
        for _ in range(n_boot):
            ra = [rng.choice(a) for _ in a]
            rb = [rng.choice(b) for _ in b]
            boots.append(statistics.median(rb) / statistics.median(ra) - 1)
        boots.sort()
        low, high = boots[int(0.05 * n_boot)], boots[int(0.95 * n_boot) - 1]
    return Verdict(rise, p, low, high, p < alpha and rise > tolerance)


def power(a_pool, b_pool, n, trials=200, seed=1, shift=0.0, **kw):
    """Fraction of gates, each on n runs drawn from each pool, that flag B. Given the same pool twice, each gate draws
    2n distinct runs and splits them, which gives the false-alarm rate (two fixed halves of a pool would carry their
    own chance difference into every gate); `shift` adds a fixed amount to every B run (a regression of known size on
    the machine's own noise)."""
    rng = random.Random(seed)
    flagged = 0
    for t in range(trials):
        if b_pool is a_pool:                   # one pool: each gate draws 2n distinct runs and splits them
            both = rng.sample(a_pool, 2 * n)
            a, b = both[:n], [x + shift for x in both[n:]]
        else:
            a = rng.sample(a_pool, n)
            b = [x + shift for x in rng.sample(b_pool, n)]
        flagged += compare(a, b, seed=t, n_perm=200, n_boot=0, **kw).regression
    return flagged / trials


def runs_needed(cv, rise, alpha=0.05, beta=0.10):
    """Runs per side for a one-sided test of a rise in the median of per-run values with coefficient of variation cv:
    n = 2 (z_alpha + z_beta)^2 (1.2533 cv / rise)^2 (1.2533: the median's efficiency against the mean, for normal
    data)."""
    z = statistics.NormalDist().inv_cdf
    return 2 * (z(1 - alpha) + z(1 - beta)) ** 2 * (1.2533 * cv / rise) ** 2


# -- certification ------------------------------------------------------------------------------------------------
def _engine():
    import firm_exchsim as x
    import firm_exchsim_codec as c
    from firm_exchsim_engine import Engine
    e = Engine(x.ExchangeConfig().engine_config())
    nt = c.NT
    e.process(1, 0, nt["ctl"]["S"]("O"))
    e.process(2, 0, nt["ctl"]["L"](1, 1, "Y"))
    e.process(2, 0, nt["ctl"]["L"](2, 2, "N"))
    e.process(3, 0, nt["ctl"]["P"](0, "T", "    "))
    return e, nt


def certify(script, engine=None):
    """script: [{"step", "session", "msg": [type, fields...] or {"ctl": [...]}, "expect": [[kind, reason or ""], ...]}]
    Each step sends one message and compares the kinds (and reasons) of the reports to the session with the expected
    ones, in order. Returns (step, ok, got) per step."""
    e, nt = engine or _engine()
    out = []
    t = 1_000
    for s in script:
        t += 1_000
        if "ctl" in s:
            _, reps = e.process(t, 0, nt["ctl"][s["ctl"][0]](*s["ctl"][1:]))
        else:
            m = s["msg"]
            _, reps = e.process(t, s.get("session", 1), nt["in"][m[0]](*m[1:]))
        got = []
        for sess, r in reps:
            if sess == s.get("session", 1):
                k = type(r).__name__[-1]
                got.append([k, getattr(r, "reason", "")])
        ok = got == s["expect"]
        out.append((s["step"], ok, got))
    return out


def load_script(path):
    return json.loads(pathlib.Path(path).read_text())


# -- deployment preflight -----------------------------------------------------------------------------------------
def preflight(root, plan):
    """Runs firm.tuneaudit (chapter 13) on the host: a deployment that needs a tuned host stops on any failure."""
    import firm_tuneaudit as ta
    findings = ta.audit(root, plan)
    return not ta.failures(findings), findings
