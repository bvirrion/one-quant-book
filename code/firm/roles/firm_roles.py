"""firm.roles -- role cards and one analysis per role (build of One Quant Book 17, chapters 16-25).

A role card records what a role is for, in data: the kinds of employer that have it, the horizon of its decisions, what
it owns of the profit and loss, whom it reports to, the occupation codes and job-title patterns that find it in labour
filings, and the books of this series that teach it. Each chapter of Part III adds its card and one analysis; this
module holds both.

Chapter 16 (trader): the supervision load of one person watching many trading algorithms. Alerts arrive as a Poisson
stream at `a` per strategy per hour; each takes a handling time; the supervisor handles them one at a time. With
exponential handling (mean h) the queue is M/M/1 (Book 4, chapter 8) and the waiting time exceeds t with probability
rho * exp(-(mu - lam) t); with any other handling the Lindley recursion W_{k+1} = max(0, W_k + S_k - A_{k+1})
simulates it.

Chapter 18 (bank quants): the four bank quant cards; a reporting-line check of a validator's independence from the
model's developer and owner, graded as the ECB guide to internal models grades organisational arrangements; and the
hours of validation an inventory of tiered models needs a year, and so the validators it employs.

API (stable):
    RoleCard(name, firm_types, horizon, pnl, reports_to, soc_codes, title_patterns, books, chapter)
    REGISTRY; register(card); card(name)
    lca_cells(ranges_rows, role, fy) -> {kind: cell}
    mm1_wait_tail(lam, mu, t) ; max_strategies(a, h, t, p) ; lindley_tail(lam, service, t, n, rng)
    mmc_wait_tail(c, lam, mu, t)
    periods_to_significance(sr, periods_per_year, z) ; years_to_significance ; fundamental_law_sr(ic, breadth, ppy)
    chain(boss, node) ; independence(boss, senior, validator, developer, owner) -> 'a' | 'b' | 'c' | 'fail'
    validation_hours(counts, full_hours, review_hours, interval_years, change_rate) ; validator_headcount(..., hours)
"""
import math
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class RoleCard:
    name: str
    firm_types: tuple
    horizon: str
    pnl: str            # what the role owns of the P&L: owns, shares, supports, none
    reports_to: str
    soc_codes: tuple
    title_patterns: tuple
    books: tuple        # series books that teach the role, as 'Book n, chapter m' strings
    chapter: int


REGISTRY = {}


def register(c: RoleCard):
    if c.name in REGISTRY:
        raise ValueError(f"role {c.name!r} already registered")
    REGISTRY[c.name] = c
    return c


def card(name):
    return REGISTRY[name]


def lca_cells(rows, role, fy=2025, level="all"):
    """Rows of data/industry/lca_ranges.csv (as dicts) -> {kind: dict(n, employers, suppressed, p10..p90)}."""
    out = {}
    for r in rows:
        if int(r["fy"]) == fy and r["role"] == role and r["level"] == level:
            cell = {"n": int(r["n"]), "employers": int(r["employers"]), "suppressed": r["suppressed"] == "1"}
            if not cell["suppressed"]:
                cell.update({k: float(r[k]) for k in ("p10", "p25", "p50", "p75", "p90")})
            out[r["kind"]] = cell
    return out


register(RoleCard(
    "trader", ("market maker", "bank", "hedge fund", "platform"), "seconds to days", "owns",
    "head of desk", ("13-2099.01", "13-2051", "41-3031"), ("TRADER", "TRADING ANALYST", "ALGORITHMIC TRAD"),
    ("Book 1, chapter 2", "Book 10, chapter 24", "Book 11, chapter 27"), 16))


def mm1_wait_tail(lam, mu, t):
    """P(wait > t) in an M/M/1 queue with arrival rate lam and service rate mu (same time unit as t)."""
    if lam >= mu:
        return 1.0
    return (lam / mu) * math.exp(-(mu - lam) * t)


def max_strategies(a, h, t, p):
    """Largest number of strategies, each alerting at rate a per hour, that one supervisor with exponential handling
    of mean h seconds can watch with P(an alert waits more than t seconds) <= p."""
    mu = 3600.0 / h
    n = 0
    while mm1_wait_tail((n + 1) * a, mu, t / 3600.0) <= p:
        n += 1
    return n


def lindley_tail(lam, service, t, n, rng):
    """Simulated P(wait > t) for Poisson arrivals at rate lam and service times drawn by service(k, rng)."""
    gaps = rng.exponential(1.0 / lam, n)
    s = service(n, rng)
    w = np.empty(n)
    w[0] = 0.0
    for k in range(1, n):
        w[k] = max(0.0, w[k - 1] + s[k - 1] - gaps[k])
    return float((w[n // 10:] > t).mean())


def mmc_wait_tail(c, lam, mu, t):
    """P(wait > t) with c supervisors sharing one queue (M/M/c, Erlang C)."""
    a = lam / mu
    if a >= c:
        return 1.0
    top = a ** c / math.factorial(c) / (1.0 - a / c)
    erlang = top / (sum(a ** k / math.factorial(k) for k in range(c)) + top)
    return erlang * math.exp(-(c * mu - lam) * t)


register(RoleCard(
    "quant researcher", ("systematic fund", "market maker", "platform", "bank", "asset manager"), "seconds to months",
    "shares (credit for signals)", "head of research or portfolio manager", ("13-2099.01", "15-2041", "15-2031"),
    ("QUANT RESEARCH", "QUANTITATIVE ANALYST", "RESEARCHER"), ("Book 7, chapter 1", "Book 7, chapter 15",
                                                              "Book 16, chapter 9"), 17))


def periods_to_significance(sr, periods_per_year, z=1.96):
    """Periods of data needed before an estimated Sharpe ratio of true value sr (annual) is z standard errors from zero,
    with IID returns: n = z^2 (1 + s^2 / 2) / s^2 where s is the per-period Sharpe ratio (Lo 2002)."""
    s = sr / math.sqrt(periods_per_year)
    return z * z * (1.0 + s * s / 2.0) / (s * s)


def years_to_significance(sr, periods_per_year, z=1.96):
    return periods_to_significance(sr, periods_per_year, z) / periods_per_year


def fundamental_law_sr(ic, breadth, periods_per_year):
    """Annual Sharpe ratio of a signal with per-bet skill ic over `breadth` independent bets a period (Grinold)."""
    return ic * math.sqrt(breadth * periods_per_year)


for _name, _titles, _socs, _books, _pnl, _to in (
        ("desk strategist", ("STRAT", "DESK QUANT", "QUANTITATIVE STRATEGIST"), ("13-2099.01", "15-2041"),
         ("Book 5, chapter 27", "Book 9, chapter 24", "Book 9, chapter 28"), "supports", "head of the trading desk"),
        ("library quant", ("QUANTITATIVE ANALYTICS", "QUANT LIBRARY", "QUANTITATIVE DEVELOPER"),
         ("13-2099.01", "15-1252"),
         ("Book 5, chapter 28", "Book 6, chapter 29"), "none", "head of quantitative analytics"),
        ("risk quant", ("MARKET RISK", "COUNTERPARTY RISK", "RISK ANALYTICS"), ("13-2054", "13-2099.01"),
         ("Book 6, chapter 21", "Book 6, chapter 23"), "none", "chief risk officer"),
        ("model validator", ("MODEL VALIDATION", "MODEL RISK"), ("13-2054", "13-2099.01", "15-2041"),
         ("Book 6, chapter 26", "Book 12, chapter 21"), "none", "head of model risk management")):
    register(RoleCard(_name, ("bank",), "days to years", _pnl, _to, _socs, _titles, _books, 18))


def chain(boss, node):
    """Managers of `node` up to the top, nearest first; `boss` maps each person or unit to its manager (None at top)."""
    out, seen = [], {node}
    while boss.get(node) is not None:
        node = boss[node]
        if node in seen:
            raise ValueError(f"reporting cycle at {node!r}")
        out.append(node)
        seen.add(node)
    return out


def independence(boss, senior, validator, developer, owner=None):
    """How far a model's validator is from its developer (and owner), as the ECB guide's three arrangements:
    'a' different members of senior management; 'b' different units under the same senior manager; 'c' separate
    staff in one unit; 'fail' if the validator reports, directly or not, to the developer or the owner."""
    up = chain(boss, validator)
    if developer in up or (owner is not None and owner in up):
        return "fail"

    def seat(node):
        path = [node] + chain(boss, node)
        for i, n in enumerate(path):
            if n in senior:
                return n, (path[i - 1] if i > 0 else n)
        return None, path[-1]

    (sv, uv), (sd, ud) = seat(validator), seat(developer)
    if sv != sd:
        return "a"
    return "b" if uv != ud else "c"


def validation_hours(counts, full_hours, review_hours, interval_years, change_rate):
    """Hours a year of independent validation for an inventory of counts[tier] models: a full validation every
    interval_years[tier], a lighter periodic review in the other years, and a full validation of the share
    change_rate of models materially changed each year."""
    total = 0.0
    for t, n in counts.items():
        k = interval_years[t]
        total += n * (full_hours[t] / k + review_hours[t] * (1.0 - 1.0 / k) + change_rate * full_hours[t])
    return total


def validator_headcount(counts, full_hours, review_hours, interval_years, change_rate, productive_hours):
    return validation_hours(counts, full_hours, review_hours, interval_years, change_rate) / productive_hours


# --- Chapter 19 (quant developer): three cards, a job-title normaliser, a title-by-code cross-tabulation and the gap
# between two populations' medians with a bootstrap interval.
#     normalise_title(title) -> (clean title, seniority) ; crosstab(pairs, min_cell) ; median_gap(x, y, rng, n_boot)

for _name, _titles, _books, _to in (
        ("research engineer", ("RESEARCH ENGINEER", "QUANTITATIVE DEVELOPER"),
         ("Book 7, chapter 1", "Book 15, chapter 1"), "head of research"),
        ("library developer", ("QUANTITATIVE DEVELOPER", "LIBRARY DEVELOPER"),
         ("Book 5, chapter 28", "Book 6, chapter 29"), "head of quantitative analytics"),
        ("trading-system developer", ("QUANTITATIVE DEVELOPER", "LOW LATENCY", "TRADING SYSTEMS"),
         ("Book 13, chapter 1", "Book 16, chapter 21"), "head of trading technology")):
    register(RoleCard(_name, ("market maker", "systematic fund", "platform", "bank"), "microseconds to days",
                      "supports", _to, ("15-1252", "13-2099.01"), _titles, _books, 19))

SENIORITY = (("MANAGING DIRECTOR", "managing director"), ("EXECUTIVE DIRECTOR", "executive director"),
             ("VICE PRESIDENT", "vice president"), ("VP", "vice president"), ("PRINCIPAL", "principal"),
             ("STAFF", "staff"), ("LEAD", "lead"), ("SENIOR", "senior"), ("SR", "senior"), ("ASSOCIATE", "associate"),
             ("JUNIOR", "junior"), ("JR", "junior"), ("GRADUATE", "junior"), ("ENTRY LEVEL", "junior"))
ABBREVIATIONS = (("QUANTS", "QUANTITATIVE"), ("QUANT", "QUANTITATIVE"), ("DEVS", "DEVELOPER"), ("DEV", "DEVELOPER"),
                 ("ENGR", "ENGINEER"), ("ENG", "ENGINEER"), ("SWE", "SOFTWARE ENGINEER"), ("SDE", "SOFTWARE ENGINEER"),
                 ("ML", "MACHINE LEARNING"), ("SW", "SOFTWARE"), ("MGR", "MANAGER"), ("ANAL", "ANALYST"))


def normalise_title(title):
    """Upper case; split at a comma, slash, bar, parenthesis or spaced dash and keep the first part that names a job
    (the others are team, desk or location); take seniority words out of every part; expand abbreviations; drop grade
    numerals (I, II, 2, L3). Returns (clean title, seniority or '')."""
    import re

    seniority, found = "", ""
    raw = str(title or "").upper().replace("C++", "CPP").replace("C#", "CSHARP")
    for part in re.split(r"\s[-\u2013]\s|[,/|()]", raw):
        words = [w for w in re.sub(r"[^A-Z0-9 ]", " ", part).split() if not re.fullmatch(r"(I{1,3}|IV|V|L?\d+)", w)]
        t = " " + " ".join(words) + " "
        for key, level in SENIORITY:
            if f" {key} " in t:
                seniority = seniority or level
                t = t.replace(f" {key} ", " ")
        for key, full in ABBREVIATIONS:
            t = t.replace(f" {key} ", f" {full} ")
        if not found and t.strip():
            found = " ".join(t.split())
    return found, seniority


def crosstab(pairs, min_cell=10):
    """Counts of (row, column) pairs; cells under min_cell are returned as None (suppressed)."""
    out = {}
    for a, b in pairs:
        out[(a, b)] = out.get((a, b), 0) + 1
    return {k: (v if v >= min_cell else None) for k, v in out.items()}


def median_gap(x, y, rng, n_boot=2000, min_cell=10):
    """Median of x minus median of y and their ratio, with 95% percentile-bootstrap intervals (independent resamples
    of each population); None if either has fewer than min_cell values."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    if len(x) < min_cell or len(y) < min_cell:
        return None
    mx = np.median(x[rng.integers(0, len(x), (n_boot, len(x)))], axis=1)
    my = np.median(y[rng.integers(0, len(y), (n_boot, len(y)))], axis=1)
    d, r = mx - my, mx / my
    return {"diff": float(np.median(x) - np.median(y)), "diff_lo": float(np.percentile(d, 2.5)),
            "diff_hi": float(np.percentile(d, 97.5)), "ratio": float(np.median(x) / np.median(y)),
            "ratio_lo": float(np.percentile(r, 2.5)), "ratio_hi": float(np.percentile(r, 97.5))}


# --- Chapter 20 (software engineer): the engineering cards and the ratio of two wage distributions percentile by
# percentile (for published percentiles, where no values are available to resample).
#     percentile_ratio(a, b, keys) -> {key: a[key] / b[key]} ; top-coded or missing values give None

for _name, _titles, _books, _to in (
        ("low-latency engineer", ("LOW LATENCY", "SOFTWARE ENGINEER", "CPP DEVELOPER"),
         ("Book 13, chapter 1", "Book 14, chapter 1"), "head of trading technology"),
        ("FPGA engineer", ("FPGA", "HARDWARE ENGINEER"), ("Book 14, chapter 6", "Book 14, chapter 7"),
         "head of hardware"),
        ("site reliability engineer", ("SITE RELIABILITY", "SRE", "PRODUCTION ENGINEER"),
         ("Book 15, chapter 28", "Book 16, chapter 21"), "head of infrastructure")):
    register(RoleCard(_name, ("market maker", "systematic fund", "platform", "bank", "exchange"),
                      "nanoseconds to days", "supports", _to, ("15-1252", "15-1299.08", "17-2061"), _titles, _books,
                      20))


def percentile_ratio(a, b, keys=("p10", "p25", "p50", "p75", "p90")):
    """Ratio of two published wage distributions at each percentile; a value that is not a number (a survey's
    top-code mark or a missing cell) gives None at that percentile."""
    out = {}
    for k in keys:
        try:
            out[k] = float(a[k]) / float(b[k])
        except (TypeError, ValueError, ZeroDivisionError):
            out[k] = None
    return out


# --- Chapter 21 (machine learning and data): the cards, Poisson intervals for filing counts, and a growth rate with
# its standard error from counts over years.
#     poisson_interval(n, level) -> (lo, hi) ; filing_trend(years, counts) -> dict(rate, se, annual, lo, hi)

for _name, _titles, _books, _to in (
        ("data scientist", ("DATA SCIENTIST", "DATA SCIENCE"), ("Book 12, chapter 1", "Book 12, chapter 28"),
         "head of data science or research"),
        ("data engineer", ("DATA ENGINEER", "DATA PLATFORM"), ("Book 15, chapter 2", "Book 15, chapter 4"),
         "head of data"),
        ("machine-learning engineer", ("MACHINE LEARNING", "ML ENGINEER"), ("Book 12, chapter 28",),
         "head of machine learning")):
    register(RoleCard(_name, ("bank", "systematic fund", "platform", "market maker", "exchange"), "days to months",
                      "supports", _to, ("15-2051", "15-1252", "15-1243"), _titles, _books, 21))


def poisson_interval(n, level=0.95):
    """Exact (Garwood) interval for a Poisson mean from one observed count n."""
    from scipy.stats import chi2

    a = 1.0 - level
    lo = 0.0 if n == 0 else chi2.ppf(a / 2, 2 * n) / 2
    return float(lo), float(chi2.ppf(1 - a / 2, 2 * n + 2) / 2)


def filing_trend(years, counts, z=1.96):
    """Log-linear growth of counts over years by Poisson-weighted least squares (weights = counts): continuous rate g,
    its standard error, and the annual compound rate exp(g) - 1 with a z-interval. With two years it reduces to
    log(n1 / n0) / (t1 - t0) and se sqrt(1/n0 + 1/n1) / (t1 - t0)."""
    t, n = np.asarray(years, float), np.asarray(counts, float)
    w = n
    tb = np.sum(w * t) / np.sum(w)
    sxx = np.sum(w * (t - tb) ** 2)
    g = float(np.sum(w * (t - tb) * np.log(n)) / sxx)
    se = float(math.sqrt(1.0 / sxx))
    return {"rate": g, "se": se, "annual": math.exp(g) - 1.0, "lo": math.exp(g - z * se) - 1.0,
            "hi": math.exp(g + z * se) - 1.0}


# --- Chapter 22 (portfolio manager and pod analyst): the cards and the portfolio manager's deal on a platform, on
# Book 16's firm.podshop pods: a share of the pod's own profit above carried losses, a salary that is an advance on it,
# a two-step drawdown ladder over the whole tenure (cut the capital, then stop the pod and end the job).
#     pm_deal(sr, years, vol, capital, rate, salary, cut, stop, n, rng, days) -> dict(pay, stopped, stop_day, pnl)

for _name, _to, _pnl in (("portfolio manager", "chief investment officer or head of strategy", "owns"),
                         ("sub-portfolio manager", "portfolio manager", "owns a share"),
                         ("pod analyst", "portfolio manager", "supports")):
    register(RoleCard(_name, ("platform", "hedge fund", "asset manager"), "days to months", _pnl, _to,
                      ("13-2051", "13-2099.01", "11-3031"), ("PORTFOLIO MANAGER", "ANALYST"),
                      ("Book 8, chapter 28", "Book 16, chapter 3", "Book 16, chapter 25"), 22))


def pm_deal(sr, years, vol, capital, rate, salary, cut, stop, n, rng, days=252):
    """Simulate n tenures of `years` for a portfolio manager whose pod earns an annual Sharpe ratio sr at annual
    volatility vol (fractions of capital). Each year-end the manager is paid max(salary, rate * max(profit - carried
    losses, 0) * capital); a drawdown from the tenure's peak above `cut` halves the capital for the rest of the tenure,
    above `stop` ends the job (salary to that day, no payout for the year, nothing after). Returns pay in dollars."""
    import pathlib
    import sys

    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "podshop"))
    import firm_podshop as ps

    daily = ps.pods(n, years, sr, vol, 0.0, rng, days)["daily"]
    size, eq, peak, carry = np.ones(n), np.zeros(n), np.zeros(n), np.zeros(n)
    alive, stop_day = np.ones(n, bool), np.full(n, years * days)
    pay, year_pnl, pnl = np.zeros(n), np.zeros(n), np.zeros(n)
    for t in range(years * days):
        step = np.where(alive, size * daily[t], 0.0)
        eq += step
        year_pnl += step
        peak = np.maximum(peak, eq)
        dd = peak - eq
        size = np.where(alive & (dd > cut), 0.5, size)
        out = alive & (dd > stop)
        pay += np.where(out, salary * ((t % days) + 1) / days, 0.0)
        stop_day = np.where(out, t, stop_day)
        alive &= ~out
        if (t + 1) % days == 0:
            net = year_pnl - carry
            pay += np.where(alive, np.maximum(salary, rate * np.maximum(net, 0.0) * capital), 0.0)
            carry = np.where(alive, np.maximum(-net, 0.0), carry)
            pnl += year_pnl
            year_pnl[:] = 0.0
    return {"pay": pay, "stopped": ~alive, "stop_day": stop_day, "pnl": (pnl + year_pnl) * capital}


# --- Chapter 23 (structurer, sales and sales-trader): the cards, and the structuring margin of a note on Book 5's
# firm.autocall: fair value per 100, the margin at a given coupon, and the coupon that leaves a target margin.
#     note_value(sheet, r, q, vol, n, seed, steps) ; structuring_margin(make_sheet, coupon, target, r, q, vol, ...)

for _name, _to, _pnl, _codes in (
        ("structurer", "head of structuring", "shares (the desk's)", ("13-2099.01", "13-2051", "41-3031")),
        ("institutional salesperson", "head of sales", "credited with client revenue", ("41-3031",)),
        ("sales-trader", "head of sales-trading", "credited with client flow", ("41-3031", "13-2099.01"))):
    register(RoleCard(_name, ("bank", "broker"), "hours to years", _pnl, _to, _codes,
                      ("STRUCTUR", "SALES"), ("Book 5, chapter 18", "Book 9, chapter 28", "Book 1, chapter 2"), 23))


def note_value(sheet, r, q, vol, n=100_000, seed=23, steps=12):
    """Fair value per 100 of a single-index autocallable term sheet under flat volatility (firm.autocall)."""
    import pathlib
    import sys

    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "autocall"))
    import firm_autocall as ac

    times, perf = ac.simulate(lambda t, s: np.full_like(s, vol), 1.0, sheet.maturity, r, q, n, seed,
                              steps_per_year=steps)
    cf = ac.cashflows(sheet, times, perf, r)
    return float(cf["pv"].mean()), cf


def structuring_margin(make_sheet, coupon, target, r, q, vol, n=100_000, seed=23, steps=12):
    """Margin per 100 sold at par at `coupon`, and the coupon that leaves `target`: the value is linear in the coupon
    along common random numbers, so two valuations (coupon 0 and `coupon`) give both."""
    v0, _ = note_value(make_sheet(0.0), r, q, vol, n, seed, steps)
    v1, cf = note_value(make_sheet(coupon), r, q, vol, n, seed, steps)
    slope = (v1 - v0) / coupon
    return {"value": v1, "margin": 100.0 - v1, "fair_coupon": (100.0 - target - v0) / slope,
            "zero_margin_coupon": (100.0 - v0) / slope, "called_first": float(np.mean(cf["called_at"] == 0)),
            "ki": float(cf["ki"].mean())}


# --- Chapter 24 (control functions): the cards, and pay mix as a share of fixed pay.
#     fixed_share(variable_to_fixed) ; mix_gap(control_ratio, business_ratio) -> dict(fixed shares, ratio of ratios)

for _name, _to, _codes in (("risk manager", "chief risk officer", ("13-2054", "13-2099.01")),
                           ("product controller", "chief financial officer", ("13-2011", "13-2051")),
                           ("compliance officer", "head of compliance", ("13-1041", "23-1011")),
                           ("operations analyst", "chief operating officer", ("43-4011", "13-2099"))):
    register(RoleCard(_name, ("bank", "market maker", "systematic fund", "platform", "exchange"), "days to months",
                      "none", _to, _codes, (_name.upper(),), ("Book 6, chapter 27", "Book 16, chapter 12"), 24))


def fixed_share(variable_to_fixed):
    """Share of total pay that is fixed, from the ratio of variable to fixed pay: 1 / (1 + v)."""
    return 1.0 / (1.0 + float(variable_to_fixed))


def mix_gap(control_ratio, business_ratio):
    return {"fixed_control": fixed_share(control_ratio), "fixed_business": fixed_share(business_ratio),
            "ratio_of_ratios": float(control_ratio) / float(business_ratio)}


# --- Chapter 25 (leadership): the cards, the UK senior management functions by firm tier (FCA guide, July 2019
# update), and a new partner's economics on Book 16's firm.partnership capital accounts.
#     SMF_TIERS ; smf_count(tier) ; partner_path(...) -> dict(draws (n, years), capital (n, years))

for _name, _to, _pnl in (("head of desk", "head of business", "owns (the desk's)"),
                         ("chief risk officer", "chief executive and the board", "none"),
                         ("partner", "the partnership", "shares (points)"),
                         ("chief executive", "the board or the partners", "answers for all")):
    register(RoleCard(_name, ("market maker", "bank", "hedge fund", "platform", "exchange"), "months to years", _pnl,
                      _to, ("11-1011", "11-3031", "11-1021"), (_name.upper(),),
                      ("Book 16, chapter 2", "Book 16, chapter 6", "Book 16, chapter 12"), 25))

SMF_TIERS = {
    "limited scope": ("SMF16", "SMF17", "SMF29"),
    "core": ("SMF1", "SMF3", "SMF9", "SMF16", "SMF17", "SMF27"),
    "enhanced": ("SMF1", "SMF2", "SMF3", "SMF4", "SMF5", "SMF7", "SMF9", "SMF10", "SMF11", "SMF12", "SMF13", "SMF14",
                 "SMF16", "SMF17", "SMF18", "SMF24", "SMF27"),
}


def smf_count(tier):
    return len(SMF_TIERS[tier])


def partner_path(mean, sd, partners, points, new_points, contribution, payout, admit_year, admit, years, n, rng):
    """n five-year paths (or `years`) of a new partner in a partnership of `partners` members with `points` each: firm
    profit each year normal(mean, sd); profit allocated by points, `payout` of a positive share drawn and the rest
    retained in the capital account, a loss allocated by points against capital; in year `admit_year` (1-based)
    `admit` more partners join with new_points each. Returns the new partner's draws and year-end capital."""
    import pathlib
    import sys

    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "partnership"))
    import firm_partnership as fp

    profits = rng.normal(mean, sd, (n, years))
    draws, capital = np.zeros((n, years)), np.zeros((n, years))
    for i in range(n):
        p = fp.Partnership([fp.Member(f"p{k}", points) for k in range(partners)] + [fp.Member("new", new_points,
                                                                                            contribution)])
        for t in range(years):
            if t + 1 == admit_year:
                p.members += [fp.Member(f"a{k}", new_points) for k in range(admit)]
            draws[i, t] = p.allocate(profits[i, t], payout)["new"]
            capital[i, t] = next(m.capital for m in p.members if m.name == "new")
    return {"draws": draws, "capital": capital, "profits": profits}
