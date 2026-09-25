"""firm.synthmkt -- the synthetic daily equity universe (build of One Quant Book 7, chapter 5).

The book's cross-sectional sandbox: a seeded market of stocks, day by day, whose returns have the stylised facts of
real ones and whose predictors have known sources. Every research tool of Books 7-9 that needs a cross-section of
stocks runs on it; the truth it keeps (the expected-return components, the market's conditional variance, the true
earnings surprises) is what makes their results checkable.

Returns. For a stock i listed on day t,
    r_it = beta_i m_t + f_{ind(i),t} + x_i . s_t + a_it + e_it
* m_t, the market factor: GJR-GARCH(1,1) with Student-t innovations (heavy tails, volatility clustering, the
  leverage effect); its conditional variance h_t scales the industry factors and, less, the specific returns, so that
  correlations rise when volatility does;
* f, industry factor returns; s_t, style factor returns (size, value, momentum) with exposures x_i;
* a_it, the planted expected return (truth), the sum of four components kept separately in `alpha`:
  momentum (a persistent drift), value (a premium on the z-scored book-to-price), post-earnings drift (after each
  announcement, a drift in the direction of the surprise) and reversal (minus a fraction of the previous day's
  specific shock: liquidity provision);
* e_it, specific shocks: Student-t, heterogeneous volatility, with a jump on earnings days.
Listings end by performance (a cumulative log return below a barrier: -30% delisting return) or by cash merger (at a
premium); each is replaced the next day by a new listing, so about n names are listed every day. Prices split when
high; payers pay quarterly dividends; volume follows turnover, the size of the move, the volatility state and
earnings days. Fundamentals are quarterly, filed with a lag, and sometimes restated later.

API (stable; the interface Books 8 and 9 code against, see code/firm/INTERFACES.md section 4):
    MarketConfig(...)                  parameters; defaults: 1,000 names, 2,520 days (ten years of 252), seed 1
    simulate(cfg) -> Panel             everything below, deterministic for a seed
    Panel fields (T days x M listings, M >= n; NaN where not listed):
        ret, price, volume, shares, listed (bool); ids (permanent ids = column index), start, end (listing days)
        industry (M,), beta (M,), style_x (M, 3) (the exposures on the LAST day: value moves daily and momentum
            monthly; for point-in-time exposures use point_in_time_styles), spec_vol (M,) daily
        mkt (T,), h (T,) market conditional variance, ind (T, K), style (T, 3)
        alpha: dict name -> (T, M) expected return for day t + 1 known at the close of day t (truth)
        delist: {pid: (day, reason, delisting return)}; splits [(day, pid, ratio)]; dividends [(day, pid, amount)]
        earnings [(day, pid, true surprise)]; fundamentals: list of dict(pid, field, fiscal_end, filed, value,
            restated, restated_value) with field in {"book", "eps"}; restated = -1 when never restated
        secmaster: firm_secmaster.SecurityMaster with tickers over time
        customer (M,): the listing's customer (permanent id), -1 if none; None unless cfg.link_share > 0. A
            supplier's return then includes link_beta / link_days times its customer's specific shocks of the last
            link_days days (alpha["link"], the truth for customer-momentum signals)
        with cfg.ou_share > 0, each listing's specific return also carries a mean-reverting level y (an AR(1) with
            coefficient exp(-1 / tau), tau lognormal across names around ou_tau days) whose innovations take ou_share
            of the specific variance; alpha["ou"] = (exp(-1 / tau) - 1) y is its expected pull (for s-score studies)
        twin (M,): with cfg.twin_share > 0, pairs of initial listings that are close substitutes: the second copies the
            first's industry, beta, size, specific volatility and book-to-price, and while both are listed its return is
            the first's times exp(the change of a stationary AR(1) log spread with mean-reversion time twin_tau and
            standard deviation twin_sd); its own announcements are then dropped from `earnings`; alpha["twin"] is the
            spread's expected pull. twin[i] is the partner's id, -1 if none; None unless cfg.twin_share > 0.
    Panel.returns_known(t)             (M,) returns of day t (what a researcher knows at the close)
    point_in_time_styles(P)            {'size' (M,), 'log_bp' (T, M), 'momentum' (T, M)}: size as at listing; log
                                       book-to-price at the close of each day from the latest first-filed book value
                                       rolled forward with returns (NaN before a filing); the momentum score in force
                                       on each day (z of the 12-1 month log return, set every 21 days from day 252, as
                                       the simulation sets it). Style exposures a researcher could have computed.
    Panel.fundamentals_store()         the fundamentals in a firm_pit.Store keyed (pid, field, fiscal_end, filed day)
"""
from __future__ import annotations

import math
import pathlib
import string
import sys
from dataclasses import dataclass, field

import numpy as np

_FIRM = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_FIRM / "secmaster"))
sys.path.insert(0, str(_FIRM / "pit"))
from firm_pit import Store  # noqa: E402
from firm_secmaster import SecurityMaster  # noqa: E402

YEAR = 252
STYLES = ("size", "value", "momentum")


@dataclass(frozen=True)
class MarketConfig:
    n: int = 1000
    days: int = 10 * YEAR
    seed: int = 1
    n_industries: int = 10
    mkt_premium: float = 0.06          # annual expected excess return of the market factor
    mkt_vol: float = 0.16              # annual unconditional volatility of the market factor
    garch_alpha: float = 0.02
    garch_gamma: float = 0.10          # leverage: extra reaction to negative shocks
    garch_beta: float = 0.92
    t_df: float = 5.0
    ind_vol: float = 0.08              # annual volatility of each industry factor
    style_vol: tuple = (0.05, 0.05, 0.07)
    style_premium: tuple = (0.0, 0.02, 0.03)
    spec_vol: float = 0.25             # median annual specific volatility
    spec_disp: float = 0.35            # log dispersion of specific volatilities across names
    spec_df: float = 4.0
    vol_link: float = 0.5              # specific volatility scales as (h_t / h_bar) ** (vol_link / 2)
    mom_sd: float = 0.12               # annual cross-sectional sd of the persistent drift
    mom_half_life: float = 504.0       # days
    value_premium: float = 0.03        # annual return per unit z-score of book-to-price
    pead: float = 0.012                # drift over 60 days per unit of standardised surprise
    earn_jump: float = 3.0             # earnings-day shock, in daily specific volatilities per unit surprise
    reversal: float = 0.05             # share of yesterday's specific shock reversed today
    barrier: float = -1.6
    merger_rate: float = 0.02          # annual probability of a cash takeover
    merger_premium: float = 0.25
    split_above: float = 250.0
    payer_share: float = 0.6
    filing_lag: tuple = (20, 55)       # days after the fiscal quarter's end
    restate_prob: float = 0.05
    link_share: float = 0.0            # share of listings that are suppliers with one customer (0: no links)
    link_beta: float = 0.1             # supplier's total response to its customer's specific shock
    link_days: int = 21                # the response is spread evenly over the next link_days days
    pead_break: int | None = None      # from this day on, post-earnings drift is multiplied by pead_after
    pead_after: float = 1.0
    ou_share: float = 0.0              # share of specific variance that is a mean-reverting (OU) level (0: none)
    ou_tau: float = 20.0               # median mean-reversion time of that level, days
    ou_disp: float = 0.8               # log dispersion of the mean-reversion times across names
    twin_share: float = 0.0            # share of the initial listings paired as close substitutes (0: none)
    twin_tau: float = 10.0             # mean-reversion time of a pair's log price spread, days
    twin_sd: float = 0.02              # stationary standard deviation of that spread


@dataclass
class Panel:
    cfg: MarketConfig
    ret: np.ndarray
    price: np.ndarray
    volume: np.ndarray
    shares: np.ndarray
    listed: np.ndarray
    start: np.ndarray
    end: np.ndarray
    industry: np.ndarray
    beta: np.ndarray
    style_x: np.ndarray
    spec_vol: np.ndarray
    mkt: np.ndarray
    h: np.ndarray
    ind: np.ndarray
    style: np.ndarray
    alpha: dict
    delist: dict
    splits: list
    dividends: list
    earnings: list
    fundamentals: list
    secmaster: SecurityMaster = field(repr=False, default=None)
    customer: np.ndarray = field(repr=False, default=None)
    twin: np.ndarray = field(repr=False, default=None)

    @property
    def ids(self) -> np.ndarray:
        return np.arange(self.ret.shape[1])

    def returns_known(self, t: int) -> np.ndarray:
        return self.ret[t]

    def fundamentals_store(self) -> Store:
        s = Store()
        for f in self.fundamentals:
            s.put(f["pid"], f["field"], f["fiscal_end"], f["filed"], f["value"])
            if f["restated"] >= 0:
                s.put(f["pid"], f["field"], f["fiscal_end"], f["restated"], f["restated_value"])
        return s


def _student(rng, df, size):
    """Student-t draws scaled to unit variance."""
    return rng.standard_t(df, size) * math.sqrt((df - 2.0) / df)


def _tickers(rng):
    letters = np.array(list(string.ascii_uppercase))
    seen = set()
    while True:
        t = "".join(rng.choice(letters, int(rng.integers(3, 5))))
        if t not in seen:
            seen.add(t)
            yield t


def simulate(cfg: MarketConfig | None = None) -> Panel:
    cfg = cfg or MarketConfig()
    rng = np.random.default_rng(cfg.seed)
    T, n, K = cfg.days, cfg.n, cfg.n_industries
    cap = n + int(n * 0.25 * T / YEAR) + 64            # room for the replacements
    # ---------------------------------------------------------------- market, industries, styles
    h_bar = cfg.mkt_vol**2 / YEAR
    persist = cfg.garch_alpha + 0.5 * cfg.garch_gamma + cfg.garch_beta
    omega = h_bar * (1.0 - persist)
    mkt, h = np.empty(T), np.empty(T)
    ht, mu = h_bar, cfg.mkt_premium / YEAR
    z = _student(rng, cfg.t_df, T)
    for t in range(T):
        h[t] = ht
        mkt[t] = mu + math.sqrt(ht) * z[t]
        shock = mkt[t] - mu
        ht = omega + (cfg.garch_alpha + cfg.garch_gamma * (shock < 0)) * shock * shock + cfg.garch_beta * ht
    state = np.sqrt(h / h_bar)
    ind = (cfg.ind_vol / math.sqrt(YEAR)) * state[:, None] * rng.standard_normal((T, K))
    style = (np.array(cfg.style_premium) / YEAR
             + (np.array(cfg.style_vol) / math.sqrt(YEAR)) * rng.standard_normal((T, 3)))
    # ---------------------------------------------------------------- per-listing arrays
    ret = np.full((T, cap), np.nan)
    price = np.full((T, cap), np.nan)
    volume = np.full((T, cap), np.nan)
    shares = np.full((T, cap), np.nan)
    listed = np.zeros((T, cap), bool)
    alpha = {k: np.full((T, cap), np.nan) for k in ("momentum", "value", "pead", "reversal")}
    start, end = np.full(cap, -1), np.full(cap, -1)
    industry = rng.integers(0, K, cap)
    beta = np.clip(rng.normal(1.0, 0.3, cap), 0.2, 2.2)
    spec_vol = cfg.spec_vol / math.sqrt(YEAR) * np.exp(rng.normal(0.0, cfg.spec_disp, cap))
    style_x = np.zeros((cap, 3))
    style_x[:, 0] = rng.normal(0.0, 1.0, cap)                       # size exposure (z)
    log_bp = rng.normal(math.log(0.6), 0.5, cap)                     # latent log book-to-price at listing
    turnover = np.exp(rng.normal(math.log(0.006), 0.5, cap))         # daily shares traded / shares outstanding
    payer = rng.random(cap) < cfg.payer_share
    yld = rng.uniform(0.01, 0.04, cap)
    earn_off = rng.integers(0, 63, cap)                              # announcement day within each quarter
    phi = 0.5 ** (1.0 / cfg.mom_half_life)
    d_sd = cfg.mom_sd / YEAR
    drift = rng.normal(0.0, d_sd, cap)
    px = np.exp(rng.normal(math.log(30.0), 0.6, cap))
    sh = np.exp(rng.normal(math.log(80e6), 1.0, cap))
    cum = np.zeros(cap)
    cumhist = np.zeros((T, cap))                                     # cumulative log return, end of each day
    last_e = np.zeros(cap)
    pead_left = np.zeros(cap)
    pead_rate = np.zeros(cap)
    eps = rng.uniform(0.5, 3.0, cap)                                 # quarterly earnings per share
    delist, splits, dividends, earnings, fundamentals = {}, [], [], [], []
    sm = SecurityMaster()
    fresh = _tickers(rng)
    alive = list(range(n))
    nxt = n
    for p in alive:
        start[p] = 0
        sm.list(p, next(fresh), 0)
    links = cfg.link_share > 0                                       # own generator: the default stream is unchanged
    if links:
        lrng = np.random.default_rng(cfg.seed + 7919)
        customer = np.full(cap, -1)
        c0 = lrng.integers(0, n - 1, n)
        c0[c0 >= np.arange(n)] += 1
        customer[:n] = np.where(lrng.random(n) < cfg.link_share, c0, -1)
        ering, esum = np.zeros((cfg.link_days, cap)), np.zeros(cap)
        alpha["link"] = np.full((T, cap), np.nan)
    ou = cfg.ou_share > 0                                            # own generator: the default stream is unchanged
    if ou:
        orng = np.random.default_rng(cfg.seed + 104729)
        ou_phi = np.exp(-1.0 / np.exp(orng.normal(math.log(cfg.ou_tau), cfg.ou_disp, cap)))
        ou_y = np.zeros(cap)
        alpha["ou"] = np.full((T, cap), np.nan)
    twins = cfg.twin_share > 0                                       # own generator: the default stream is unchanged
    if twins:
        trng = np.random.default_rng(cfg.seed + 15485863)
        k2 = int(cfg.twin_share * n / 2)
        pick = trng.permutation(n)[:2 * k2]
        tw_p, tw_q = pick[:k2], pick[k2:]
        twin = np.full(cap, -1)
        twin[tw_p], twin[tw_q] = tw_q, tw_p
        for arr in (industry, beta, spec_vol, log_bp):              # the substitute copies its partner
            arr[tw_q] = arr[tw_p]
        style_x[tw_q, 0] = style_x[tw_p, 0]
        tw_phi = math.exp(-1.0 / cfg.twin_tau)
        tw_s = np.zeros(k2)
        is_q = np.zeros(cap, bool)
        is_q[tw_q] = True
        alpha["twin"] = np.full((T, cap), np.nan)
    # ---------------------------------------------------------------- day by day
    for t in range(T):
        a = np.array(alive)
        # expected return for day t (known at the close of t - 1), recorded at t - 1 as the forecast for t
        z_bp = (log_bp[a] - log_bp[a].mean()) / (log_bp[a].std() + 1e-12)
        style_x[a, 1] = z_bp
        if t % 21 == 0 and t >= YEAR:                               # momentum exposure: z of the 12-1 month return
            full = start[a] <= t - YEAR
            past = cumhist[t - 22, a] - cumhist[t - YEAR - 1, a]
            zm = np.zeros(len(a))
            if full.sum() > 10:
                zm[full] = (past[full] - past[full].mean()) / (past[full].std() + 1e-12)
            style_x[a, 2] = zm
        comp = {"momentum": drift[a], "value": cfg.value_premium / YEAR * z_bp,
                "pead": np.where(pead_left[a] > 0, pead_rate[a], 0.0),
                "reversal": -cfg.reversal * last_e[a]}
        if links:                                                    # the customer's shocks, diffused with a delay
            c = customer[a]
            comp["link"] = np.where(c >= 0, cfg.link_beta / cfg.link_days * esum[np.maximum(c, 0)], 0.0)
        if ou:                                                       # the level's expected pull toward zero
            comp["ou"] = (ou_phi[a] - 1.0) * ou_y[a]
        if twins:                                                    # a substitute's return is its partner's
            where = np.full(cap, -1)
            where[a] = np.arange(len(a))
            both = (where[tw_p] >= 0) & (where[tw_q] >= 0)
            ip, iq = where[tw_p[both]], where[tw_q[both]]
            for v in comp.values():
                v[iq] = v[ip]
            comp["twin"] = np.zeros(len(a))
            comp["twin"][iq] = (tw_phi - 1.0) * tw_s[both]
        if t > 0:
            for k, v in comp.items():
                alpha[k][t - 1, a] = v
        exp_ret = sum(comp.values())
        sv = spec_vol[a] * state[t] ** cfg.vol_link
        e = sv * _student(rng, cfg.spec_df, len(a))
        if ou:
            e *= math.sqrt(1.0 - cfg.ou_share)
            xi = math.sqrt(cfg.ou_share) * sv * orng.standard_normal(len(a))
        # earnings day: a true surprise, a jump in its direction, then a drift
        is_earn = (t % 63) == earn_off[a]
        if is_earn.any():
            idx = np.flatnonzero(is_earn)
            s = rng.standard_normal(len(idx))
            e[idx] += cfg.earn_jump * sv[idx] * s
            pa = a[idx]
            k = cfg.pead_after if cfg.pead_break is not None and t >= cfg.pead_break else 1.0
            pead_left[pa], pead_rate[pa] = 60, k * cfg.pead * s / 60.0
            for p, sur in zip(pa, s, strict=True):
                earnings.append((t, int(p), float(sur)))
            eps[pa] *= np.exp(0.03 * s)
        pead_left[a] = np.maximum(pead_left[a] - 1, 0)
        if links:
            slot = t % cfg.link_days
            esum -= ering[slot]
            ering[slot] = 0.0
            ering[slot, a] = e
            esum += ering[slot]
        r = (beta[a] * mkt[t] + ind[t, industry[a]] + style_x[a] @ style[t] + exp_ret + e)
        if ou:
            r = r + xi
            ou_y[a] = ou_phi[a] * ou_y[a] + xi
        if twins and both.any():                                     # plus the change of a stationary log spread
            ds = (tw_phi - 1.0) * tw_s[both] + cfg.twin_sd * math.sqrt(1 - tw_phi**2) * trng.standard_normal(len(ip))
            tw_s[both] += ds
            r[iq] = (1.0 + np.maximum(r[ip], -0.95)) * np.exp(ds) - 1.0
            e[iq] = e[ip]
        r = np.maximum(r, -0.95)
        last_e[a] = e
        drift[a] = phi * drift[a] + math.sqrt(1 - phi * phi) * rng.normal(0.0, d_sd, len(a))
        log_bp[a] += -np.log1p(r) + rng.normal(0.0, 0.002, len(a))  # book moves slowly, price moves daily
        cum[a] += np.log1p(r)
        cumhist[t] = cum
        # listings that end today
        merged = rng.random(len(a)) < cfg.merger_rate / YEAR
        failed = (cum[a] < cfg.barrier) & ~merged
        new_px = px[a] * (1.0 + r)
        # dividends (quarterly, on a fixed day of the quarter, for payers)
        pay = payer[a] & ((t % 63) == ((earn_off[a] + 20) % 63))
        div = np.where(pay, yld[a] / 4.0 * px[a], 0.0)
        new_px = new_px - div
        ret[t, a] = r
        ret[t, a[failed]] = -0.30
        ret[t, a[merged]] = (1.0 + r[merged]) * (1.0 + cfg.merger_premium) - 1.0
        price[t, a] = new_px
        vol_mult = (1.0 + 2.0 * np.abs(e) / sv) * state[t] ** 0.5 * np.where(is_earn, 3.0, 1.0)
        volume[t, a] = np.round(sh[a] * turnover[a] * vol_mult * np.exp(rng.normal(0.0, 0.25, len(a))))
        shares[t, a] = sh[a]
        listed[t, a] = True
        for p, d in zip(a[pay], div[pay], strict=True):
            dividends.append((t, int(p), float(d)))
        px[a] = new_px
        # splits
        big = np.flatnonzero(px[a] > cfg.split_above)
        for j in big:
            p = a[j]
            px[p] /= 2.0
            sh[p] *= 2.0
            eps[p] /= 2.0
            splits.append((t, int(p), 2))
        # quarterly fundamentals: fiscal quarters end on days 0, 63, 126, ...; filed with a lag
        if t % 63 == 0 and t > 0:
            lag = rng.integers(cfg.filing_lag[0], cfg.filing_lag[1] + 1, len(a))
            restate = rng.random(len(a)) < cfg.restate_prob
            book = px[a] * np.exp(log_bp[a])
            for j, p in enumerate(a):
                for fld, val in (("book", book[j]), ("eps", eps[p])):
                    rs = int(t + lag[j] + rng.integers(60, 300)) if (restate[j] and fld == "eps") else -1
                    fundamentals.append({"pid": int(p), "field": fld, "fiscal_end": t, "filed": int(t + lag[j]),
                                         "value": float(val), "restated": rs,
                                         "restated_value": float(val * math.exp(rng.normal(0.0, 0.1)))})
        # replace the listings that ended
        gone = list(a[failed]) + list(a[merged])
        for p in a[failed]:
            delist[int(p)] = (t, "performance", -0.30)
            sm.delist(int(p), t, "performance", -0.30)
        for p in a[merged]:
            delist[int(p)] = (t, "merger", float(ret[t, p]))
            sm.delist(int(p), t, "merger", float(ret[t, p]))
        for p in gone:
            end[p] = t
        if gone:
            keep = set(alive) - set(int(g) for g in gone)
            for _ in gone:
                if nxt >= cap:
                    break
                start[nxt] = t + 1
                sm.list(nxt, next(fresh), t + 1)
                if links and lrng.random() < cfg.link_share:
                    customer[nxt] = int(lrng.choice(sorted(keep)))
                keep.add(nxt)
                nxt += 1
            alive = sorted(keep)
    M = nxt
    if twins:                                        # a twinned substitute's own announcements did not move it
        live = lambda p, d: end[p] < 0 or end[p] >= d  # noqa: E731
        earnings = [x for x in earnings if not (is_q[x[1]] and live(twin[x[1]], x[0]) and live(x[1], x[0]))]
    for p in range(M):
        if end[p] < 0:
            end[p] = T - 1
    cut = lambda x: x[:, :M]  # noqa: E731
    return Panel(cfg, cut(ret), cut(price), cut(volume), cut(shares), cut(listed), start[:M], end[:M],
                 industry[:M], beta[:M], style_x[:M], spec_vol[:M], mkt, h, ind, style,
                 {k: cut(v) for k, v in alpha.items()}, delist, splits, dividends, earnings, fundamentals, sm,
                 customer[:M] if links else None, twin[:M] if twins else None)


def point_in_time_styles(P: Panel) -> dict:
    """Style descriptors as they could have been known: see the module docstring."""
    T, M = P.ret.shape
    cum = np.cumsum(np.nan_to_num(np.log1p(np.where(P.listed, P.ret, 0.0))), axis=0)
    split_day = {(t, p): r for t, p, r in P.splits}
    anchor = np.full((T, M), np.nan)
    for f in P.fundamentals:
        if f["field"] != "book" or f["filed"] >= T:
            continue
        p, fe = f["pid"], f["fiscal_end"]
        px = P.price[fe, p] / split_day.get((fe, p), 1)
        if np.isfinite(px) and px > 0:
            anchor[f["filed"], p] = math.log(f["value"] / px) + cum[fe, p]
    idx = np.where(np.isfinite(anchor), np.arange(T)[:, None], 0)
    idx = np.maximum.accumulate(idx, axis=0)
    filled = anchor[idx, np.arange(M)[None, :]]
    log_bp = np.where(P.listed, filled - cum, np.nan)
    mom = np.zeros((T, M))
    cur = np.zeros(M)
    for t in range(T):
        if t % 21 == 0 and t >= YEAR:
            a = P.listed[t]
            full = a & (P.start <= t - YEAR)
            past = cum[t - 22] - cum[t - YEAR - 1]
            cur = np.where(a, 0.0, cur)
            if full.sum() > 10:
                cur[full] = (past[full] - past[full].mean()) / (past[full].std() + 1e-12)
        mom[t] = cur
    return {"size": P.style_x[:, 0].copy(), "log_bp": log_bp, "momentum": np.where(P.listed, mom, 0.0)}
