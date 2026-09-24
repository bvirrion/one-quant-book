"""Book 3, Chapter 15: proof of reserves with a Merkle sum tree, what it does not prove, the FTX.com
shortfall at the petition time, fee arithmetic and a burst of requests under a rate-limit governor."""
import csv
import hashlib
import pathlib
import random
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/ratelimit"))
from firm_ratelimit import binance_like  # noqa: E402


def h(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode()).hexdigest()


def leaf(account: str, nonce: str, balance: int) -> tuple[str, int]:
    """A leaf commits to the account, a secret nonce and the balance (in the smallest unit)."""
    return h(account, nonce, str(balance)), balance


def build(leaves: list[tuple[str, int]]) -> list[list[tuple[str, int]]]:
    """Merkle sum tree: each node hashes its children and the sum of their balances."""
    levels = [leaves]
    while len(levels[-1]) > 1:
        lv = levels[-1] + ([("0" * 64, 0)] if len(levels[-1]) % 2 else [])
        levels.append([(h(lv[i][0], lv[i + 1][0], str(lv[i][1] + lv[i + 1][1])), lv[i][1] + lv[i + 1][1])
                       for i in range(0, len(lv), 2)])
    return levels


def proof(levels, i: int) -> list[tuple[str, int, bool]]:
    """Siblings on the path from leaf i to the root: (hash, sum, sibling is on the left)."""
    path = []
    for lv in levels[:-1]:
        lv = lv + ([("0" * 64, 0)] if len(lv) % 2 else [])
        j = i ^ 1
        path.append((lv[j][0], lv[j][1], j < i))
        i //= 2
    return path


def verify(node: tuple[str, int], path, root: tuple[str, int], check_sums: bool = True) -> bool:
    """Recompute the root from a leaf and its path; optionally refuse any negative sum on the way."""
    hh, s = node
    for sh, ss, left in path:
        if check_sums and ss < 0:
            return False
        hh = h(sh, hh, str(ss + s)) if left else h(hh, sh, str(s + ss))
        s += ss
    return (hh, s) == root


def customers(n: int = 1023, seed: int = 15) -> list[int]:
    """Illustrative balances in cents: lognormal, a few large accounts."""
    rng = random.Random(seed)
    return [int(100 * rng.lognormvariate(7.0, 1.6)) for _ in range(n)]


def fake_negative(balances: list[int], share: float = 0.6, slot: int = 0):
    """The exchange hides a share of its liabilities by inserting one fake account with a negative balance
    at position `slot`. Returns (true total, published total, customers whose proofs pass hash-only
    checks, customers whose proofs pass when sums are checked)."""
    total = sum(balances)
    fake = -int(share * total)
    accts = balances[:slot] + [fake] + balances[slot:]
    leaves = [leaf(f"acct{i}", f"n{i}", b) for i, b in enumerate(accts)]
    levels = build(leaves)
    root = levels[-1][0]
    real = [i for i in range(len(accts)) if i != slot]
    hash_only = sum(verify(leaves[i], proof(levels, i), root, check_sums=False) for i in real)
    with_sums = sum(verify(leaves[i], proof(levels, i), root, check_sums=True) for i in real)
    return total, root[1], hash_only, with_sums


def omitted(p_check: float, k: int) -> float:
    """Probability that omitting k accounts is caught when each customer checks with probability p."""
    return 1 - (1 - p_check) ** k


def ftx_coverage(path: str | None = None) -> dict[str, float]:
    """Shares of FTX.com customer claims covered at the petition time (filing totals, USD millions)."""
    path = path or str(ROOT / "data/markets-3/ftx_com_petition_balances.csv")
    rows = list(csv.DictReader(open(path)))
    pay_a = sum(int(r["customer_payables"]) for r in rows if r["category"] == "A")
    assert abs(pay_a - 10_544) <= 3            # rows are rounded; the filing's totals are used below
    return {"located_A": 694 / 10_544, "with_receivables_A": 1_078 / 10_544,
            "all_assets": 2_540 / 11_233, "cash_stable": 580 / 6_991, "deficit": 8_693}


def round_trip_bp(maker_bp: float, taker_bp: float, maker_legs: int) -> float:
    """Cost of a buy and a sell in basis points when `maker_legs` of the two rest as maker orders."""
    return maker_legs * maker_bp + (2 - maker_legs) * taker_bp


def burst(seconds: int = 300, instruments: int = 5, coalesce: bool = False):
    """Quote updates (orders of weight 1) under the governor's 100-orders-per-10-seconds rule: 5 a
    second, 25 a second in a volatile minute (seconds 60 to 119), spread over `instruments`. Queued
    updates are sent in order; with `coalesce` only the latest update per instrument is kept. Returns
    rows (second, orders sent that second, backlog at the end of the second, age in seconds of the
    oldest queued update)."""
    g = binance_like()
    queue: list[tuple[int, int]] = []                 # (instrument, second created)
    rows, k = [], 0
    for s in range(seconds):
        for _ in range(25 if 60 <= s < 120 else 5):
            item = (k % instruments, s)
            k += 1
            if coalesce:
                queue = [q for q in queue if q[0] != item[0]]
            queue.append(item)
        sent = 0
        while queue and g.try_send(1000 * s + sent, 1, True)[0]:
            queue.pop(0)
            sent += 1
        rows.append((s, sent, len(queue), s - queue[0][1] if queue else 0))
    return rows
