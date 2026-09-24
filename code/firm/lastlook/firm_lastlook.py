"""Last-look simulation and transaction-cost analysis (build of Book 2, Chapter 15).

A liquidity provider streams a two-way price, half-spread `half` (basis points) around its view
of the mid. A client request at the quoted price is held for `hold` milliseconds; the provider then
compares the mid with the mid at the quote. With an asymmetric check it rejects requests whose
price has moved in the client's favour by more than `threshold`; with a symmetric check, moves in
either direction. Moves are in basis points, positive in the client's favour; the mid follows a
Brownian motion of `sigma` basis points per square-root millisecond. Some clients are informed:
they trade only after a move of `edge` basis points the provider's quote has not yet reflected.
"""
import math
import random
from dataclasses import dataclass


@dataclass(frozen=True)
class Request:
    informed: bool
    move_at_decision: float    # client-favourable move from the quote's mid to the end of the hold
    move_after: float          # client-favourable move from the quote's mid to `horizon` after the hold
    accepted: bool


def check(move: float, threshold: float, policy: str) -> bool:
    """True if the request is accepted."""
    if policy == "none":
        return True
    if policy == "asymmetric":
        return move <= threshold
    return abs(move) <= threshold                            # symmetric


def simulate(n: int, sigma: float, hold: float, threshold: float, policy: str, informed_share: float = 0.0,
             edge: float = 0.0, horizon: float = 1000.0, seed: int = 1) -> list[Request]:
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        informed = rng.random() < informed_share
        jump = edge if informed else 0.0
        at_decision = jump + rng.gauss(0.0, sigma * math.sqrt(hold))
        after = at_decision + rng.gauss(0.0, sigma * math.sqrt(horizon))
        out.append(Request(informed, at_decision, after, check(at_decision, threshold, policy)))
    return out


def tca(requests: list[Request], half: float) -> dict[str, float]:
    """Fill ratio, reject rates by client type, and the provider's mark-out per filled request
    (half-spread earned less the client-favourable move by the horizon), in basis points."""
    filled = [r for r in requests if r.accepted]
    inf = [r for r in requests if r.informed]
    uninf = [r for r in requests if not r.informed]

    def reject_rate(rs: list[Request]) -> float:
        return sum(not r.accepted for r in rs) / len(rs) if rs else 0.0

    return {"fill_ratio": len(filled) / len(requests), "reject_informed": reject_rate(inf),
            "reject_uninformed": reject_rate(uninf),
            "markout": sum(half - r.move_after for r in filled) / len(filled) if filled else 0.0,
            "client_gain_filled": sum(r.move_at_decision for r in filled) / len(requests)}


def expected_transfer(sigma: float, hold: float, threshold: float, policy: str) -> float:
    """Expected client-favourable move given up per request by rejections, uninformed flow:
    E[move * 1{rejected}] for move ~ N(0, sigma^2 * hold)."""
    s = sigma * math.sqrt(hold)
    phi = math.exp(-0.5 * (threshold / s) ** 2) / math.sqrt(2 * math.pi)
    if policy == "asymmetric":
        return s * phi                                       # E[X 1{X > t}]
    return 0.0                                               # symmetric: the two tails cancel
