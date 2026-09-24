"""Chapter 27 of Book 2: getting access to FX. A day of a fund's orders routed through the
prime-broker limit gate, and the allocation of its flow and overnight position across three prime
brokers that keeps every limit at least cost. Limits, fees and charges are illustrative."""
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/pblimits"))
from firm_pblimits import Book, Order, read_limits, route

FIRM = pathlib.Path(__file__).resolve().parents[3] / "firm/pblimits"

USD = {"USD": 1.0, "EUR": 1.10, "JPY": 1 / 150, "GBP": 1.30, "MXN": 1 / 18}
RATES = {"EURUSD": 1.10, "USDJPY": 150.0, "GBPUSD": 1.30, "USDMXN": 18.0}
# The problem: daily flow (USD millions) by the prime brokers allowed to take it, and the position.
FLOW = {"majors": (1000.0, "ABC"), "GBPUSD": (150.0, "BC"), "USDMXN": (50.0, "C")}
POSITION = {"majors": (270.0, "ABC"), "MXN": (30.0, "C")}
NOP_CHARGE = {"A": 30.0, "B": 20.0, "C": 50.0}          # USD per million of overnight NOP per day
DAYS = 250


def limits() -> dict[str, tuple[float, float, float]]:
    """pb -> (fee per million, settlement capacity in millions, NOP capacity in millions)."""
    return {lim.pb: (lim.fee_per_m, lim.settle_limit / 1e6, lim.nop_limit / 1e6)
            for lim in read_limits(str(FIRM / "limits.csv"))}


def greedy(demand: dict[str, tuple[float, str]], price: dict[str, float], cap: dict[str, float]):
    """Fill the most constrained demand first, each from its cheapest allowed provider with room."""
    room, alloc = dict(cap), {pb: 0.0 for pb in cap}
    for _, (amount, allowed) in sorted(demand.items(), key=lambda kv: len(kv[1][1])):
        for pb in sorted(allowed, key=lambda p: price[p]):
            take = min(amount, room[pb])
            alloc[pb] += take
            room[pb] -= take
            amount -= take
        if amount > 1e-9:
            raise ValueError("infeasible")
    return alloc


def plan() -> dict[str, object]:
    lim = limits()
    fee = {pb: v[0] for pb, v in lim.items()}
    flow = greedy(FLOW, fee, {pb: v[1] for pb, v in lim.items()})
    pos = greedy(POSITION, NOP_CHARGE, {pb: v[2] for pb, v in lim.items()})
    fee_cost = sum(fee[pb] * flow[pb] for pb in flow)
    nop_cost = sum(NOP_CHARGE[pb] * pos[pb] for pb in pos)
    all_c = fee["C"] * sum(a for a, _ in FLOW.values()) + NOP_CHARGE["C"] * sum(a for a, _ in POSITION.values())
    flow_c = fee["C"] * sum(a for a, _ in FLOW.values())
    pos_c = NOP_CHARGE["C"] * sum(a for a, _ in POSITION.values())
    return {"flow": flow, "position": pos, "fee_cost": fee_cost, "nop_cost": nop_cost,
            "total": fee_cost + nop_cost, "year": DAYS * (fee_cost + nop_cost), "all_c": all_c,
            "bars": [("all at C", flow_c, pos_c), ("fees optimised", fee_cost, pos_c),
                     ("NOP optimised", flow_c, nop_cost), ("both optimised", fee_cost, nop_cost)]}


def brute_force(step: float = 10.0) -> float:
    """Cheapest feasible cost over a grid of flow and position splits, to check the greedy plan."""
    lim = limits()
    fee = {pb: v[0] for pb, v in lim.items()}
    best = float("inf")
    majors, gbp, mxn = FLOW["majors"][0], FLOW["GBPUSD"][0], FLOW["USDMXN"][0]
    n = int(majors / step)
    for i in range(n + 1):                                   # majors to A
        for j in range(n + 1 - i):                           # majors to B
            a, b, c = i * step, j * step, majors - (i + j) * step
            for g in range(int(gbp / step) + 1):             # GBP to B
                gb, gc = g * step, gbp - g * step
                xa, xb, xc = a, b + gb, c + gc + mxn
                if xa <= lim["A"][1] and xb <= lim["B"][1] and xc <= lim["C"][1]:
                    best = min(best, fee["A"] * xa + fee["B"] * xb + fee["C"] * xc)
    pos_best = float("inf")
    m, mx = POSITION["majors"][0], POSITION["MXN"][0]
    for i in range(int(m / step) + 1):
        for j in range(int(m / step) + 1 - i):
            ya, yb, yc = i * step, j * step, m - (i + j) * step + mx
            if ya <= lim["A"][2] and yb <= lim["B"][2] and yc <= lim["C"][2]:
                pos_best = min(pos_best, NOP_CHARGE["A"] * ya + NOP_CHARGE["B"] * yb + NOP_CHARGE["C"] * yc)
    return best + pos_best


def day_of_orders(n: int = 240, seed: int = 27, nop_a: float | None = None) -> dict[str, object]:
    """Route a seeded day of orders, with a drift that builds long EUR and short JPY positions."""
    rng = random.Random(seed)
    books = [Book(lim) for lim in read_limits(str(FIRM / "limits.csv"))]
    if nop_a is not None:
        books[0].limits.nop_limit = nop_a
    pairs = ["EURUSD"] * 6 + ["USDJPY"] * 3 + ["GBPUSD"] * 2 + ["USDMXN"]
    path, rejected, where = [], 0, {"A": 0, "B": 0, "C": 0}
    for t in range(n):
        pair = rng.choice(pairs)
        buy = rng.random() < (0.62 if pair == "EURUSD" else 0.4 if pair == "USDJPY" else 0.5)
        usd_size = rng.choice([2, 5, 5, 10, 10, 20]) * 1e6
        amount = usd_size / USD[pair[:3]]
        pb, _ = route(books, Order(pair, buy, amount, RATES[pair], 2), USD)
        if pb is None:
            rejected += 1
        else:
            where[pb] += usd_size
        path.append((t + 1, *(100 * b.nop() / b.limits.nop_limit for b in books)))
    first_full = next((t for t, a, *_ in path if a >= 100 - 1e-9), None)
    return {"path": path, "rejected": rejected, "gross": where, "first_full_a": first_full,
            "nop": {b.limits.pb: b.nop() for b in books}}
