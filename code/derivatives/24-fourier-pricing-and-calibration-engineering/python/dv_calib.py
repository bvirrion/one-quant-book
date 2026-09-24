"""Fourier pricing and calibration engineering (Book 5, Chapter 24): COS against Carr-Madan against a reference,
a daily Heston calibration over 60 synthetic days with and without a penalty on parameter changes, the weights,
the profile of the fit along the volatility of volatility, a round-trip test and the recalibration P&L of a
volatility swap."""
import functools
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/jumps"))
sys.path.insert(0, str(ROOT / "code/firm/varswap"))
sys.path.insert(0, str(ROOT / "code/firm/calib"))
from firm_calib import (  # noqa: E402
    Heston,
    QuoteSet,
    calibrate,
    carr_madan_at,
    cos_calls,
    filter_quotes,
    heston_from,
    heston_to,
    jump_alarm,
    lewis_calls,
    vol_errors,
)
from firm_jumps import Bates  # noqa: E402
from firm_varswap import heston_mean_variance, heston_vol_swap  # noqa: E402

BASE = Heston(0.04, 1.5, 0.04, 0.6, -0.7)               # chapter 10's base parameters


# ---------------------------------------------------------------- transform pricing
@functools.cache
def transform_study() -> dict:
    """Maximum price error over 17 strikes (60-140) of a one-year call, against the Gauss-Legendre reference."""
    ks = np.linspace(60.0, 140.0, 17)
    ref = lewis_calls(BASE, 100.0, ks, 1.0)
    cos = {n: float(np.abs(cos_calls(BASE, 100.0, ks, 1.0, n=n) - ref).max()) for n in (16, 32, 64, 128, 256)}
    fft = {n: float(np.abs(carr_madan_at(BASE, 100.0, ks, 1.0, n=n) - ref).max()) for n in (256, 1024, 4096, 16384)}
    narrow = float(np.abs(cos_calls(BASE, 100.0, ks, 1.0, n=256, width=12.0) - ref).max())
    return {"cos": cos, "fft": fft, "narrow": narrow, "atm": float(ref[8])}


# ---------------------------------------------------------------- the synthetic market
EXP = np.array([1 / 12, 0.25, 0.5, 1.0])
Z = np.array([-1.0, -0.5, 0.0, 0.5, 1.0])
TRUE = dict(kappa=1.5, vbar=0.04, eta=0.4, rho=-0.6, lam=0.3, mu=-0.12, delta=0.10)   # a Bates market


def grid() -> tuple[np.ndarray, np.ndarray]:
    t = np.repeat(EXP, len(Z))
    return t, 100.0 * np.exp(np.tile(Z, len(EXP)) * 0.2 * np.sqrt(t))


@functools.cache
def market(n_days: int = 60, noise: float = 0.003, seed: int = 1) -> tuple:
    """Daily quote sets: Bates implied volatilities plus quote noise, half-spreads widening with moneyness, one
    crossed and one stale (wide) quote a day at random. The ATM volatility wanders as an OU process."""
    rng = np.random.default_rng(seed)
    t, k = grid()
    v, days = 0.04, []
    for _ in range(n_days):
        m = Bates(v, **TRUE)
        iv = vol_errors(m, QuoteSet(t, k, np.full_like(t, 0.2), np.full_like(t, 0.2), 100.0)) + 0.2
        mid = iv + noise * rng.standard_normal(len(t))
        half = 0.002 + 0.002 * np.abs(np.tile(Z, len(EXP)))
        bid, ask = mid - half, mid + half
        i, j = rng.choice(len(t), 2, replace=False)
        bid[i], ask[i] = ask[i] + 0.01, bid[i]                # crossed
        ask[j] = mid[j] + 0.06                                 # stale, wide
        days.append((v, QuoteSet(t, k, bid, ask, 100.0)))
        sv = math.sqrt(v)
        sv = sv + 0.05 * (0.2 - sv) + 0.004 * rng.standard_normal()
        v = sv * sv
    return tuple(days)


@functools.cache
def first_fit():
    q = market()[0][1]
    keep, _ = filter_quotes(q)
    return calibrate(q.subset(keep), heston_to(BASE))


@functools.cache
def daily(reg: float, equal: bool = False) -> dict:
    """Calibrate every day from yesterday's parameters, with the penalty reg |z - z_yesterday|^2."""
    zp = first_fit().z.copy()
    eta, kappa, rmse, swap, conv, dropped, iters = [], [], [], [], [], [], []
    for _, q in market():
        keep, counts = filter_quotes(q)
        weights = np.ones(int(keep.sum())) if equal else None
        f = calibrate(q.subset(keep), zp, weights=weights, prior=zp if reg > 0 else None, reg=reg)
        iters.append(f.iterations)
        m = f.model
        eta.append(m.eta)
        kappa.append(m.kappa)
        rmse.append(f.rmse)
        swap.append(heston_vol_swap(m.v0, m.kappa, m.vbar, m.eta, 1.0))
        conv.append(math.sqrt(heston_mean_variance(m.v0, m.kappa, m.vbar, 1.0)) - swap[-1])
        dropped.append(sum(counts.values()))
        zp = f.z
    eta, swap, conv = np.array(eta), np.array(swap), np.array(conv)
    return {"eta": eta, "kappa": np.array(kappa), "rmse": np.array(rmse), "swap": swap, "dropped": dropped,
            "max_d_eta": float(np.max(np.abs(np.diff(eta)))), "mean_rmse": float(np.mean(rmse)),
            "sd_d_swap": float(np.std(np.diff(swap))), "iterations": iters, "conv": conv,
            "sd_d_conv": float(np.std(np.diff(conv)))}


REGS = (0.0, 1e-5, 3e-5, 1e-4, 3e-4, 1e-3, 3e-3, 1e-2)


@functools.cache
def scan() -> dict:
    base = daily(0.0)["mean_rmse"]
    rows = {r: {"max_d_eta": daily(r)["max_d_eta"], "d_rmse": daily(r)["mean_rmse"] - base} for r in REGS}
    chosen = min(r for r in REGS if rows[r]["max_d_eta"] < 0.1)
    return {"rows": rows, "chosen": chosen, "base_rmse": base}


def worst_day() -> dict:
    d = daily(0.0)
    i = int(np.argmax(np.abs(np.diff(d["eta"]))))
    r = daily(scan()["chosen"])
    return {"day": i + 1, "eta_before": float(d["eta"][i]), "eta_after": float(d["eta"][i + 1]),
            "rmse_before": float(d["rmse"][i]), "rmse_after": float(d["rmse"][i + 1]),
            "swap_move": float(d["swap"][i + 1] - d["swap"][i]),
            "swap_move_reg": float(r["swap"][i + 1] - r["swap"][i]),
            "conv_before": float(d["conv"][i]), "conv_after": float(d["conv"][i + 1]),
            "conv_move_reg": float(r["conv"][i + 1] - r["conv"][i]),
            "kappa_before": float(d["kappa"][i]), "kappa_after": float(d["kappa"][i + 1])}


# ---------------------------------------------------------------- weights, profile, round trip
@functools.cache
def weights_table() -> dict:
    """First day: fit with vega weights and with equal price weights; RMSE of volatility errors by expiry."""
    q = market()[0][1]
    keep, counts = filter_quotes(q)
    qq = q.subset(keep)
    out = {"counts": counts, "kept": int(keep.sum())}
    for name, w in (("vega", None), ("equal", np.ones(len(qq.t)))):
        f = calibrate(qq, heston_to(BASE), weights=w)
        err = vol_errors(f.model, qq)
        out[name] = {float(t): float(np.sqrt(np.mean(err[qq.t == t] ** 2))) for t in EXP}
        out[name]["all"] = float(np.sqrt(np.mean(err ** 2)))
    return out


@functools.cache
def profile(etas=(0.25, 0.35, 0.45, 0.55, 0.65, 0.8, 1.0)) -> dict:
    """Best fit with the volatility of volatility held fixed (the other four re-optimised), first day."""
    q = market()[0][1]
    keep, _ = filter_quotes(q)
    qq = q.subset(keep)
    z0 = np.delete(first_fit().z, 3)
    out = {}
    for e in etas:
        def make(z4, e=e):
            return heston_from(np.insert(z4, 3, math.log(e)))
        f = calibrate(qq, z0, make=make)
        out[e] = {"rmse": f.rmse, "kappa": f.model.kappa}
    return out


@functools.cache
def round_trip(reps: int = 20) -> dict:
    """Quotes generated by a known Heston model: without noise the fit recovers it; with 0.3 volatility point of
    noise, the spread of each fitted parameter over reps noisy copies shows which ones the quotes identify."""
    t, k = grid()
    truth = Heston(0.045, 2.0, 0.05, 0.5, -0.65)
    iv = vol_errors(truth, QuoteSet(t, k, np.full_like(t, 0.2), np.full_like(t, 0.2), 100.0)) + 0.2
    clean = calibrate(QuoteSet(t, k, iv, iv, 100.0), heston_to(BASE))
    rng = np.random.default_rng(3)
    fits = []
    for _ in range(reps):
        m = iv + 0.003 * rng.standard_normal(len(t))
        fits.append(calibrate(QuoteSet(t, k, m, m, 100.0), heston_to(truth)).model)
    arr = np.array([[f.v0, f.kappa, f.vbar, f.eta, f.rho] for f in fits])
    return {"clean": clean.model, "clean_rmse": clean.rmse, "truth": truth,
            "sd": dict(zip(("v0", "kappa", "vbar", "eta", "rho"), arr.std(axis=0), strict=True)),
            "atm_vol_sd": float(np.std(np.sqrt(arr[:, 0]))), "condition": clean.condition,
            "alarm": jump_alarm(heston_to(fits[0]), heston_to(fits[1]), [0.1] * 5)}
