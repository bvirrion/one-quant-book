"""Book 3, Chapter 16: arbitrage across synthetic venues, transfer latency as risk, two published
wash-trading tests on synthetic tapes, and the break-even of the kimchi-premium round trip."""
import math
import pathlib
import random
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/triarb"))
from firm_triarb import Quote, scan  # noqa: E402

CYCLE = [("BTC", "ETH", "USDT")]


def books(seed: int, noise_bp: float = 8.0, half_spread_bp: float = 1.0) -> dict:
    """Three venues quoting BTC/USDT, ETH/USDT and ETH/BTC around common prices, each mid off by noise."""
    rng = random.Random(seed)
    btc, eth = 60_000.0, 3_000.0
    out = {}
    for v in ("V1", "V2", "V3"):
        book = {}
        for pair, mid in (("BTC/USDT", btc), ("ETH/USDT", eth), ("ETH/BTC", eth / btc)):
            m = mid * (1 + rng.gauss(0, noise_bp) / 1e4)
            h = m * half_spread_bp / 1e4
            book[pair] = Quote(m - h, m + h, 5.0 if pair == "BTC/USDT" else 100.0, 5.0 if pair == "BTC/USDT" else 100.0)
        out[v] = book
    return out


def count_opportunities(fee: float, n: int = 500, rebalance_bp: float = 3.0) -> tuple[int, int]:
    """Across n independent snapshots: (triangular, cross-venue) opportunities that pay after fees."""
    tri = crs = 0
    for s in range(n):
        for o in scan(books(s), {"V1": fee, "V2": fee, "V3": fee}, CYCLE, rebalance_bp):
            tri += o.kind == "triangular"
            crs += o.kind == "cross"
    return tri, crs


def p_loss(gap_bp: float, cost_bp: float, minutes: float, vol_annual: float) -> float:
    """Probability that a cross-venue trade done by transferring the asset loses money: the price moves
    by a normal amount with standard deviation vol * sqrt(t) while the asset is in flight."""
    sd = 1e4 * vol_annual * math.sqrt(minutes / (365 * 24 * 60))
    return 0.5 * (1 + math.erf(-(gap_bp - cost_bp) / (sd * math.sqrt(2))))


UNIT = 10_000                                  # sizes in base units of 0.0001 BTC


def genuine_tape(n: int, seed: int = 16, p_round: float = 0.35) -> list[int]:
    """Trade sizes (units) of real traders: lognormal, a share cut to one significant figure (0.01,
    0.02, ..., 0.1, 0.2 BTC), which keeps the first digit and lands on a multiple of 100 units."""
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        s = max(1, int(round(UNIT * rng.lognormvariate(math.log(0.02), 1.5))))
        if s >= 100 and rng.random() < p_round:
            p = 10 ** (len(str(s)) - 1)
            s = s // p * p
        out.append(s)
    return out


def wash_tape(n: int, seed: int = 61) -> list[int]:
    """Machine-generated wash trades: sizes uniform between 10 and 500 units, never deliberately round."""
    rng = random.Random(seed)
    return [rng.randint(10, 500) for _ in range(n)]


def mixed_tape(n: int, wash_share: float, seed: int = 7) -> list[int]:
    k = int(wash_share * n)
    return genuine_tape(n - k, seed) + wash_tape(k, seed + 1)


def first_digits(sizes: list[int]) -> list[float]:
    """Frequencies of the first significant digit 1..9."""
    c = [0] * 10
    for s in sizes:
        c[int(str(s)[0])] += 1
    return [c[d] / len(sizes) for d in range(1, 10)]


BENFORD = [math.log10(1 + 1 / d) for d in range(1, 10)]


def benford_chi2(sizes: list[int]) -> float:
    """Pearson chi-square of the first-digit counts against Benford's law (8 degrees of freedom;
    15.5 is the 5% critical value)."""
    n = len(sizes)
    return sum((f * n - b * n) ** 2 / (b * n) for f, b in zip(first_digits(sizes), BENFORD, strict=True))


def clustering_ratio(sizes: list[int], step: int = 100, radius: int = 50) -> float:
    """Mean count at multiples of `step` over the mean count at the other sizes within `radius` of them."""
    count: dict[int, int] = {}
    for s in sizes:
        count[s] = count.get(s, 0) + 1
    centres = range(step, max(sizes) // step * step + 1, step)
    at = [count.get(c, 0) for c in centres]
    near = [count.get(c + d, 0) for c in centres for d in range(-radius, radius + 1) if d]
    return (sum(at) / len(at)) / (sum(near) / len(near))


def wash_share_estimate(sizes: list[int], benchmark: list[int], step: int = 100) -> float:
    """Rounding-based estimate: authentic trades = round trades x (1 + benchmark unrounded-to-round
    ratio); the excess of unrounded trades is wash. Trades below one step are left out."""
    def split(x):
        big = [s for s in x if s >= step]
        r = sum(s % step == 0 for s in big)
        return r, len(big) - r
    r0, u0 = split(benchmark)
    r, u = split(sizes)
    return max(0.0, 1 - r * (1 + u0 / r0) / (r + u))


def kimchi_breakeven(fee_abroad: float = 0.001, withdraw: float = 0.0005, fee_korea: float = 0.0005,
                     fx_spread: float = 0.005, repatriation: float = 0.02, minutes: float = 60,
                     vol_annual: float = 0.7, z: float = 1.65) -> float:
    """Premium below which buying abroad, transferring, selling for won and repatriating loses money.
    Costs compound; price risk during the transfer is charged as z standard deviations."""
    risk = z * vol_annual * math.sqrt(minutes / (365 * 24 * 60))
    cost_in = (1 + fee_abroad) * (1 + withdraw) * (1 + risk)
    kept = (1 - fee_korea) * (1 - fx_spread) * (1 - repatriation)
    return cost_in / kept - 1
