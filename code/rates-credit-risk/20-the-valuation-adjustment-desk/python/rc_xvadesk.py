"""Chapter 20 of Book 6: the valuation-adjustment desk. Incremental CVA of new trades in chapter 17's
netting set with chapter 18's counterparty, Euler allocation of the set's CVA, a proxy credit spread for
an unrated client from an illustrative peer table, and the all-in quote for a twenty-year swap with that
client: CVA, funding cost and capital charge as running basis points, and the part the desk can hedge."""
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for p in ("code/firm/xvaquote", "code/firm/xvafund", "code/firm/cva", "code/firm/cdscurve", "code/firm/exposure",
          "code/rates-credit-risk/18-credit-and-debit-valuation-adjustments/python"):
    sys.path.insert(0, str(ROOT / p))
import rc_cva as cv  # noqa: E402
from firm_cdscurve import bootstrap, legs  # noqa: E402
from firm_cva import cs01_buckets, cva, deflators, discounted_profiles  # noqa: E402
from firm_exposure import Swap, simulate, usd_par_rate  # noqa: E402
from firm_xvafund import IrTrade, ba_cva_capital, effective_maturity, fca, ir_addon, kva, sa_ccr_ead, scva  # noqa: E402
from firm_xvaquote import euler_cva, incremental, netting_cva, proxy_spread, running_charge  # noqa: E402

R = cv.R
DISC = cv.DISC

# ---- incremental CVA and allocation in chapter 17's netting set --------------------------------------


def _set():
    d = cv.data()
    v = cv.ex.values()
    return d, [v["swap"][:, :-1], v["xccy"][:, :-1]], d["D"][:, :-1], d["t"][:-1]


def new_swap(receive_fixed: bool, notional: float = 50e6, maturity: int = 5) -> np.ndarray:
    sc = cv.ex.scenarios()
    return Swap(notional, usd_par_rate(DISC, maturity), maturity, receive_fixed).values(sc)[:, :-1]


def incremental_table() -> dict:
    d, vals, D, t = _set()

    def adj(vs):
        return netting_cva(vs, D, t, d["cpty"], R)

    return {"pay": incremental(adj, vals, new_swap(False)), "receive": incremental(adj, vals, new_swap(True))}


def allocation() -> dict:
    d, vals, D, t = _set()
    total = netting_cva(vals, D, t, d["cpty"], R)
    alloc = euler_cva(vals, D, t, d["cpty"], R)
    standalone = [netting_cva([v], D, t, d["cpty"], R) for v in vals]
    return {"total": total, "euler": alloc, "standalone": standalone}


# ---- proxy spread for an unrated client --------------------------------------------------------------
PEERS = [  # (rating, sector, region, 10y CDS spread) -- illustrative liquid peers
    ("A", "industrials", "US", 0.0085), ("A", "industrials", "EU", 0.0095), ("A", "utilities", "US", 0.0070),
    ("A", "utilities", "EU", 0.0080), ("A", "consumer", "US", 0.0090), ("A", "consumer", "EU", 0.0100),
    ("BBB", "industrials", "US", 0.0165), ("BBB", "industrials", "EU", 0.0180), ("BBB", "utilities", "US", 0.0130),
    ("BBB", "utilities", "EU", 0.0150), ("BBB", "consumer", "US", 0.0175), ("BBB", "consumer", "EU", 0.0190),
    ("BB", "industrials", "US", 0.0340), ("BB", "industrials", "EU", 0.0370), ("BB", "utilities", "US", 0.0280),
    ("BB", "utilities", "EU", 0.0300), ("BB", "consumer", "US", 0.0360), ("BB", "consumer", "EU", 0.0400)]
CLIENT = ("BB", "industrials", "US")          # internal rating of the unrated client
SHAPE = [x / cv.CPTY[-1] for x in cv.CPTY]      # term structure borrowed from chapter 18's BBB curve


def proxy(client=CLIENT) -> dict:
    return proxy_spread(PEERS, client)


def proxy_curve(client=CLIENT):
    s10 = proxy(client)["spread"]
    return [s10 * x for x in SHAPE]


# ---- the twenty-year quote ------------------------------------------------------------------------------
NOTIONAL, MAT, S_F, HURDLE, RW_CCR, CAP_RATIO, RW_CVA_NR = 100e6, 20, 0.0080, 0.10, 1.00, 0.08, 0.07
_Q = {}


def quote_data():
    if not _Q:
        sc = simulate(cv.ex.MKT, float(MAT), 26, 4000, seed=21)
        k = usd_par_rate(DISC, MAT)
        V = Swap(NOTIONAL, k, MAT, receive_fixed=True).values(sc)[:, :-1]
        D = deflators(sc)[:, :-1]
        t = sc.times[:-1]
        dee, _ = discounted_profiles(V, D)
        ee = np.maximum(V, 0.0).mean(axis=0)
        _Q.update(t=t, dee=dee, ee=ee, k=k)
    return _Q


def annuity(maturity: int = MAT) -> float:
    return sum(DISC.df_t(float(k)) for k in range(1, maturity + 1))


def twenty_year_quote(client=CLIENT, rw_cva: float = RW_CVA_NR) -> dict:
    q = quote_data()
    t, dee, ee = q["t"], q["dee"], q["ee"]
    c = bootstrap(DISC, cv.TENORS, proxy_curve(client), R)
    out = {"k": q["k"], "cva": cva(dee, t, c, R)}
    surv = np.array([c.survival(float(x)) for x in t])
    out["fca"] = fca(dee, t, S_F, surv)
    ts = np.arange(0.0, float(MAT), 0.25)
    cap = []
    for x in ts:
        m = MAT - x
        addon = ir_addon([IrTrade("USD", NOTIONAL, 0.0, m, -1.0, m)])
        e = sa_ccr_ead(float(ee[int(np.searchsorted(t, x - 1e-9))]), addon)
        cap.append(CAP_RATIO * RW_CCR * e + ba_cva_capital([scva(rw_cva, effective_maturity(m), e)]))
    cap = np.array(cap)
    disc = np.array([DISC.df_t(float(x)) for x in ts])
    s = np.array([c.survival(float(x)) for x in ts])
    out["kva"] = kva(cap, ts, HURDLE, disc, s)
    out["capital0"] = float(cap[0])
    out["total"] = out["cva"] + out["fca"] + out["kva"]
    a = annuity()
    for key in ("cva", "fca", "kva", "total"):
        out[key + "_bp"] = 1e4 * running_charge(out[key], NOTIONAL, a)
    out["hedgeable_share"] = out["cva"] / out["total"]
    out["cs01"] = sum(cs01_buckets(dee, t, DISC, cv.TENORS, proxy_curve(client), R))
    out["hedge_notional"] = out["cs01"] / (1e-4 * legs(c, DISC, 10.0, R)[0])
    return out


def quote_profile():
    q = quote_data()
    return [(float(t), e / 1e6) for t, e in zip(q["t"], q["ee"], strict=True)][::4]


def proxy_fit_table():
    """(observed log10 spread bp, fitted, rating index) for the peers, and the client's prediction."""
    p = proxy()
    cats = [sorted({x[i] for x in PEERS}) for i in range(3)]
    out = []
    for r in PEERS:
        x = [1.0]
        for i in range(3):
            x += [1.0 if r[i] == c else 0.0 for c in cats[i][1:]]
        out.append((1e4 * r[3], 1e4 * float(np.exp(np.array(x) @ p["beta"])), r[0]))
    return out
