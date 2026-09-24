"""SABR in rates and the swaption volatility cube (build of One Quant Book 6, chapter 5).

- Hagan et al. (2002) implied-volatility expansions: lognormal (any beta, positive rates) and the
  normal-volatility form of normal SABR (beta = 0, any sign of rate);
- shifted SABR: the lognormal expansion applied to F + zeta and K + zeta, priced with Black on the
  shifted rates (a shifted lognormal model);
- calibration of one smile section by Levenberg-Marquardt (numpy only), alpha > 0 and |rho| < 1
  by reparametrisation;
- the implied density of a section (second strike derivative of the call price), to detect the
  negative densities of the expansion in the low-strike wing;
- a cube of calibrated sections on an expiry x tenor grid, interpolated bilinearly in the
  parameters to price any expiry, tenor and strike.
Volatilities and rates are decimals. Book 5's `firm_sabr` (One Quant Book 5, chapter 11) is the
equity-desk twin; the two are reconciled through the pricing library's interface.
"""
import math
import pathlib
import sys
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "normalvol"))
from firm_normalvol import bachelier, black, implied  # noqa: E402


@dataclass(frozen=True)
class Sabr:
    alpha: float
    beta: float
    rho: float
    nu: float
    shift: float = 0.0          # zeta; ignored by the normal (beta = 0) form


def _x(z: float, rho: float) -> float:
    return math.log((math.sqrt(1 - 2 * rho * z + z * z) + z - rho) / (1 - rho))


def hagan_lognormal(f: float, k: float, t: float, p: Sabr) -> float:
    """Black volatility of the shifted rates F + zeta, K + zeta (Hagan et al. 2002, eq. 2.17a)."""
    f, k = f + p.shift, k + p.shift
    if f <= 0 or k <= 0:
        raise ValueError("shifted forward and strike must be positive")
    a, b, r, n = p.alpha, p.beta, p.rho, p.nu
    fk = (f * k) ** ((1 - b) / 2)
    lfk = math.log(f / k)
    denom = fk * (1 + (1 - b) ** 2 / 24 * lfk**2 + (1 - b) ** 4 / 1920 * lfk**4)
    z = n / a * fk * lfk
    zx = 1.0 if abs(z) < 1e-12 else z / _x(z, r)
    corr = 1 + ((1 - b) ** 2 / 24 * a * a / fk**2 + r * b * n * a / (4 * fk) + (2 - 3 * r * r) / 24 * n * n) * t
    return a / denom * zx * corr


def hagan_normal_beta0(f: float, k: float, t: float, p: Sabr) -> float:
    """Normal volatility of normal SABR (beta = 0): alpha * zeta/x(zeta) * (1 + (2 - 3 rho^2) nu^2 t / 24)."""
    a, r, n = p.alpha, p.rho, p.nu
    z = n / a * (f - k)
    zx = 1.0 if abs(z) < 1e-12 else z / _x(z, r)
    return a * zx * (1 + (2 - 3 * r * r) / 24 * n * n * t)


def price(f: float, k: float, t: float, p: Sabr, annuity: float = 1.0, payer: bool = True,
          model: str = "shifted") -> float:
    if model == "normal":
        return bachelier(f, k, t, hagan_normal_beta0(f, k, t, p), annuity, payer)
    return black(f + p.shift, k + p.shift, t, hagan_lognormal(f, k, t, p), annuity, payer)


def normal_vol(f: float, k: float, t: float, p: Sabr, model: str = "shifted") -> float:
    """The model's price quoted as a normal (Bachelier) volatility."""
    if model == "normal":
        return hagan_normal_beta0(f, k, t, p)
    payer = k >= f
    return implied(price(f, k, t, p, 1.0, payer, model), f, k, t, 1.0, payer, model="normal")


def _to_params(x: np.ndarray, beta: float, shift: float) -> Sabr:
    return Sabr(math.exp(x[0]), beta, math.tanh(x[1]), math.exp(x[2]), shift)


def to_shifted_black(f: float, k: float, t: float, vol_n: float, shift: float) -> float:
    """Convert a normal-volatility quote into the Black volatility of the shifted rates."""
    payer = k >= f
    pr = bachelier(f, k, t, vol_n, 1.0, payer)
    return implied(pr, f + shift, k + shift, t, 1.0, payer, model="black")


def calibrate_section(f: float, t: float, strikes: Sequence[float], normal_vols: Sequence[float], beta: float = 0.5,
                      shift: float = 0.0, model: str = "shifted", iters: int = 200) -> tuple[Sabr, float]:
    """Fit (alpha, rho, nu) to normal-volatility quotes by Levenberg-Marquardt; beta and the shift fixed.
    The shifted model is fitted in shifted-Black volatility (quotes converted once), the normal model
    in normal volatility. Returns the parameters and the root-mean-square error in normal volatility."""
    if model == "normal":
        target = np.asarray(normal_vols, dtype=float)
        vol_fn = hagan_normal_beta0
        x = np.array([math.log(float(np.interp(f, strikes, normal_vols))), 0.0, math.log(0.3)])
    else:
        target = np.array([to_shifted_black(f, k, t, v, shift) for k, v in zip(strikes, normal_vols, strict=True)])
        vol_fn = hagan_lognormal
        atm = float(np.interp(f, strikes, target))
        x = np.array([math.log(atm * (f + shift) ** (1 - beta)), 0.0, math.log(0.3)])

    def resid(xv):
        p = _to_params(xv, beta, shift)
        try:
            return np.array([vol_fn(f, k, t, p) for k in strikes]) - target
        except (ValueError, OverflowError, ZeroDivisionError):
            return np.full(len(strikes), 1.0)
    r = resid(x)
    lam = 1e-3
    for _ in range(iters):
        jac = np.empty((len(strikes), 3))
        for j in range(3):
            e = x.copy()
            e[j] += 1e-7
            jac[:, j] = (resid(e) - r) / 1e-7
        g, h = jac.T @ r, jac.T @ jac
        step = np.linalg.solve(h + lam * np.diag(np.diag(h) + 1e-18), -g)
        xn = x + step
        rn = resid(xn)
        if rn @ rn < r @ r:
            x, r, lam = xn, rn, lam / 3
            if np.max(np.abs(step)) < 1e-12:
                break
        else:
            lam *= 5
            if lam > 1e12:
                break
    p = _to_params(x, beta, shift)
    err = [normal_vol(f, k, t, p, model) - v for k, v in zip(strikes, normal_vols, strict=True)]
    return p, float(np.sqrt(np.mean(np.square(err))))


def density(f: float, t: float, p: Sabr, strikes: Sequence[float], model: str = "shifted",
            h: float = 1e-5) -> list[float]:
    """Implied density of the rate at expiry, d2C/dK2 (per unit annuity), at each strike."""
    return [(price(f, k + h, t, p, model=model) - 2 * price(f, k, t, p, model=model)
             + price(f, k - h, t, p, model=model)) / (h * h) for k in strikes]


@dataclass
class Cube:
    """Calibrated SABR sections on a grid of expiries and tenors (years), with their forwards."""
    expiries: list[float]
    tenors: list[float]
    sections: dict          # (expiry, tenor) -> Sabr
    forwards: dict          # (expiry, tenor) -> forward swap rate
    model: str = "shifted"

    def _weights(self, e: float, n: float):
        def bracket(xs, x):
            x = min(max(x, xs[0]), xs[-1])
            i = min(max(1, int(np.searchsorted(xs, x))), len(xs) - 1)
            w = (x - xs[i - 1]) / (xs[i] - xs[i - 1])
            return xs[i - 1], xs[i], w
        e0, e1, we = bracket(self.expiries, e)
        n0, n1, wn = bracket(self.tenors, n)
        return [((e0, n0), (1 - we) * (1 - wn)), ((e1, n0), we * (1 - wn)), ((e0, n1), (1 - we) * wn),
                ((e1, n1), we * wn)]

    def params(self, e: float, n: float) -> Sabr:
        ws = self._weights(e, n)
        s0 = self.sections[ws[0][0]]
        a = sum(w * self.sections[k].alpha for k, w in ws)
        r = sum(w * self.sections[k].rho for k, w in ws)
        nu = sum(w * self.sections[k].nu for k, w in ws)
        return Sabr(a, s0.beta, r, nu, s0.shift)

    def forward(self, e: float, n: float) -> float:
        return sum(w * self.forwards[k] for k, w in self._weights(e, n))

    def normal_vol(self, e: float, n: float, k: float, f: float | None = None) -> float:
        f = self.forward(e, n) if f is None else f
        return normal_vol(f, k, e, self.params(e, n), self.model)
