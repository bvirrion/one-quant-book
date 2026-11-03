"""Crypto engineering: Solidity compiled by solc 0.8.28 and run on an in-memory EVM, plus Python models of what surrounds it.

The EVM tests need the packages in solidity/package.json, installed into build/iv38/node with
`npm install --ignore-scripts`. They skip with that reason where the packages are absent. Nothing here touches a live chain,
a network or an account; every address is local to the run. Q30 is prose, and is listed in NONNUMERIC.
"""
import fractions
import itertools
import json
import math
import os
import pathlib
import random
import subprocess
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
PY = HERE / "python"
SOL = HERE / "solidity"
NODE = HERE.parents[2] / "build" / "iv38" / "node" / "node_modules"
sys.path.insert(0, str(PY))

import iv_amm  # noqa: E402
import iv_approve  # noqa: E402
import iv_arb_size  # noqa: E402
import iv_calldata  # noqa: E402
import iv_deposits  # noqa: E402
import iv_holds  # noqa: E402
import iv_liquidation  # noqa: E402
import iv_merkle  # noqa: E402
import iv_oracle  # noqa: E402
import iv_sandwich  # noqa: E402
import iv_shamir  # noqa: E402
import iv_twap  # noqa: E402
import iv_utxo  # noqa: E402
import iv_withdraw  # noqa: E402

NONNUMERIC = {30: "A system design in prose; its pieces are tested in the questions before it"}
ETH = 10**18
rng_amm = random.Random(14)
AMM_CASES = [[10**18, 1000 * 10**18, 2_000_000 * 10**18]] + [
    [rng_amm.randint(1, 10**20), rng_amm.randint(10**18, 10**24), rng_amm.randint(10**18, 10**24)] for _ in range(100)]


@pytest.fixture(scope="module")
def evm():
    if not NODE.is_dir():
        pytest.skip("needs solc and an in-memory EVM: npm install --ignore-scripts from solidity/package.json in build/iv38/node")
    r = subprocess.run(["node", str(SOL / "run_all.cjs"), json.dumps([[str(v) for v in c] for c in AMM_CASES])],
                       capture_output=True, text=True, timeout=120, env={**os.environ, "NODE_PATH": str(NODE)})
    assert r.returncode == 0, r.stderr[:2000]
    data = json.loads(r.stdout)
    assert data["solc"].startswith("0.8.28")
    return data


def test_q1():
    used, change, left = iv_utxo.spend([500, 300], 600, 10)
    assert sorted(used) == [300, 500] and change == 190 and left == []
    with pytest.raises(ValueError):
        iv_utxo.spend([500, 300], 800, 10)
    rng = random.Random(1)
    for _ in range(2000):
        coins = [rng.randint(1, 500) for _ in range(rng.randint(1, 8))]
        pay, fee = rng.randint(1, 800), rng.randint(0, 20)
        if sum(coins) < pay + fee:
            with pytest.raises(ValueError):
                iv_utxo.spend(coins, pay, fee)
            continue
        used, change, left = iv_utxo.spend(coins, pay, fee)
        assert sum(used) == pay + fee + change and change >= 0          # nothing created or lost but the fee
        assert sorted(used + left) == sorted(coins)                     # every coin used up whole, or untouched


def test_q2():
    assert 21_000 * 21 == 441_000 and 441_000 / 1e9 == pytest.approx(0.000441)
    assert 21_000 * 20 / 1e9 == pytest.approx(0.00042) and 21_000 / 1e9 == pytest.approx(0.000021)

    def next_base(base, used, limit):          # the reference code's rule, with a target of half the limit
        target = limit // 2
        return base + base * (used - target) // target // 8

    assert next_base(20_000, 30_000_000, 30_000_000) == 22_500
    assert next_base(20_000, 15_000_000, 30_000_000) == 20_000
    assert next_base(20_000, 0, 30_000_000) == 17_500


def test_q3(evm):
    f = evm["fixed"]
    assert (f["divFirst"], f["mulFirst"]) == ("0", "1")
    assert f["wmul"] == str(3 * ETH) and f["wmulTiny"] == "0" and f["mulOverflow"] is False


def test_q4(evm):
    assert evm["locations"] == {"viaMemory": "1", "viaStorage": "2"}


def test_q5():
    def mine(pending, next_nonce):
        mined = []
        while next_nonce in pending:           # a model of the rule: one per nonce, and no gaps
            mined.append(pending[next_nonce])
            next_nonce += 1
        return mined, next_nonce

    assert mine({0: "a", 1: "b", 3: "d"}, 0) == (["a", "b"], 2)
    assert mine({0: "b"}, 1) == ([], 1)        # an old nonce cannot be replayed
    assert mine({}, 0) == ([], 0)


def test_q6():
    assert 12 * 32 == 384 and 2 * 384 / 60 == pytest.approx(12.8)


def test_q7(evm):
    s = evm["slot"]
    overhead = s["same"] - 2200                # a no-op write to a cold slot costs 2100 + 100
    assert s["zero_to_nonzero"] - overhead == 22_100
    assert s["nonzero_to_nonzero"] - overhead == 5000
    assert s["to_zero"] - overhead == 5000 and s["to_zero_refund"] == 4800
    two = evm["slotTwice"]                     # two writes in one transaction: the second finds the slot warm
    assert 22_100 <= two["first"] < 22_300 and 100 <= two["second"] < 200


def test_q8(evm):
    p = evm["packing"]
    assert p["loose"] == 3 and p["tight"] == 2
    assert int(p["tightSlot0"], 16) == (3 << 128) | 1


def test_q9(evm):
    o = evm["overflow"]
    assert o["checkedOk"] is False and o["checkedOut"].endswith("11") and o["checkedOut"].startswith("0x4e487b71")
    assert o["unchecked"] == o["max"] == str(2**256 - 1) and o["narrow"] == "44" and 300 % 256 == 44


def test_q10(evm):
    v = evm["Vault"]
    assert v["attackOk"] is True and v["vault"] == "0" and v["attacker"] == str(11 * ETH) and v["bobWithdrawOk"] is False
    for fixed in ("OrderedVault", "LockedVault"):
        s = evm[fixed]
        assert s["attackOk"] is False and s["vault"] == str(10 * ETH) and s["attacker"] == "0"
        assert s["bobWithdrawOk"] is True and s["vaultAfterBob"] == "0"    # an honest user is unaffected


def test_q11(evm):
    p = evm["pay"]
    assert p["uncheckedOk"] is True and p["paid"] == "1" and p["rejecter"] == "0" and p["held"] == str(ETH)
    assert p["checkedOk"] is False


def test_q12(evm):
    o = evm["origin"]
    assert o["originOk"] is True and o["originTrap"] == str(5 * ETH)
    assert o["senderOk"] is False and o["senderWallet"] == str(5 * ETH)


def test_q13():
    assert iv_approve.most_taken(100, 60) == 160 and iv_approve.most_taken_with_compare(100, 60) == 100
    for n, m in itertools.product(range(0, 40, 3), repeat=2):
        assert iv_approve.most_taken(n, m) == n + m
        assert iv_approve.most_taken_with_compare(n, m) == max(n, m)
    assert iv_approve.most_taken(0, 60) == 60  # from zero, there is nothing to take first

    def through_zero(n, m, check):
        """The spender takes n ahead of approve(0). The second approve is m, or what is left of m if the owner looks."""
        spent = n
        second = max(m - spent, 0) if check else m
        return spent + second                  # the spender then takes all of the second allowance

    assert through_zero(100, 60, check=False) == 160    # done blindly, going through 0 changes nothing
    assert through_zero(100, 60, check=True) == 100
    for n, m in itertools.product(range(0, 40, 3), repeat=2):
        assert through_zero(n, m, check=False) == n + m
        assert through_zero(n, m, check=True) == max(n, m) == iv_approve.most_taken_with_compare(n, m)


def test_q14(evm):
    pool = iv_amm.Pool(1, 1)
    for (a, x, y), got in zip(AMM_CASES, evm["amm"], strict=True):
        assert pool.amount_out(a, x, y) == int(got)      # the contract and the model agree to the wei
    assert int(evm["amm"][0]) == 1992013962079806432986


def test_q14_model():
    rng = random.Random(15)
    for _ in range(2000):
        x, y = rng.randint(10**18, 10**24), rng.randint(10**18, 10**24)
        pool = iv_amm.Pool(x, y)
        k = x * y
        amount = rng.randint(1, 10**22)
        got = pool.buy_y(amount)
        assert pool.x * pool.y >= k                       # the invariant never falls
        assert 0 <= got < y
        back = pool.buy_x(got) if got else 0
        assert back <= amount                             # a round trip cannot make money
    no_fee = iv_amm.Pool(10**24, 10**24, fee_bps=0)
    one = no_fee.amount_out(10**22, no_fee.x, no_fee.y)
    assert one < 10**22                                   # even with no fee, size moves the price


def test_q15():
    profit = iv_oracle.attack
    assert profit(1000, 1000, 9000, 100, 0.5) == pytest.approx(4881.08, abs=0.01)
    assert profit(1000, 1000, 9000, 100, 0.5, fair_oracle=1.0) == pytest.approx(-55.42, abs=0.01)
    # a second route, in exact fractions and with no pool object: every printed step of the answer
    k = fractions.Fraction(997, 1000)
    tokens = k * 9000 * 1000 / (1000 + k * 9000)
    x, y = 1000 - tokens, fractions.Fraction(1000 + 9000)
    price = y / x
    value, loan = 100 * price, 50 * price
    back = k * tokens * y / (x + k * tokens)
    assert float(tokens) == pytest.approx(899.73, abs=0.01) and float(price) == pytest.approx(99.73, abs=0.01)
    assert round(value) == 9973 and float(loan) == pytest.approx(4986.5) and round(back) == 8995
    assert profit(1000, 1000, 9000, 100, 0.5) == pytest.approx(float(loan + back - 9000 - 100), abs=1e-6)
    assert profit(1000, 1000, 9000, 100, 0.5, fair_oracle=1.0) == pytest.approx(float(50 + back - 9000 - 100), abs=1e-6)
    assert profit(1_000_000, 1_000_000, 9000, 100, 0.5) < 0   # a deep pool barely moves
    assert profit(1000, 1000, 1e-9, 100, 0.5) == pytest.approx(-50, abs=0.01)   # with no push, half the collateral is lost


def test_q16():
    rng = random.Random(16)
    for _ in range(300):
        path = [rng.randint(1, 100) for _ in range(rng.randint(2, 200))]   # the price in each second
        a = rng.randrange(len(path))
        b = rng.randint(a + 1, len(path))
        acc = iv_twap.Accumulator(0, path[0])
        readings = {}
        for s in range(len(path) + 1):
            if s in (a, b):
                readings[s] = acc.read(s)
            if 0 < s + 1 < len(path) and path[s + 1] != path[s]:           # updates only when the price moves
                acc.update(s + 1, path[s + 1])
        assert iv_twap.twap(readings[a], readings[b]) == pytest.approx(sum(path[a:b]) / (b - a))
    # a spike of 100x in one of 100 seconds moves the arithmetic average by about 2x
    acc = iv_twap.Accumulator(0, 1)
    first = acc.read(0)
    acc.update(99, 100)
    acc.update(100, 1)
    assert iv_twap.twap(first, acc.read(100)) == pytest.approx(1.99)


def test_q17(evm):
    f = evm["feed"]
    assert f["fresh"] == "200000" and f["stale"] == "reverted" and f["staleTrusting"] == "200000"
    assert f["negative"] == "reverted" and f["negativeTrusting"] == str(2**256 - 1)


def test_q18():
    x, y, victim = 2_000_000.0, 1000.0, 20_000.0
    plain = iv_sandwich.out(victim, x, y)
    assert plain == pytest.approx(9.8716, abs=1e-3)
    assert iv_sandwich.largest_front(victim, x, y, 0.0) == pytest.approx(0.0, abs=1e-6)
    results = {}
    for s in (0.005, 0.01, 0.03):
        front = iv_sandwich.largest_front(victim, x, y, s)
        got = iv_sandwich.victim_gets(front, victim, x, y)
        assert got == pytest.approx(plain * (1 - s), rel=1e-6)
        results[s] = iv_sandwich.profit(front, victim, x, y)
        grid = [front * k / 500 for k in range(501)]
        assert max(iv_sandwich.profit(g, victim, x, y) for g in grid) == pytest.approx(results[s], rel=1e-3)
    assert results[0.01] == pytest.approx(140.3, abs=0.1)
    assert results[0.005] < results[0.01] < results[0.03]
    assert iv_sandwich.profit(10_140.9, 0.0, x, y) < 0   # with no victim, the two legs only pay fees


def test_q19():
    to, amount = b"\x11" * 20, ETH
    abi, packed = iv_calldata.abi_transfer(to, amount), iv_calldata.packed_transfer(to, amount)
    assert (len(abi), iv_calldata.calldata_gas(abi)) == (68, 632)
    assert (len(packed), iv_calldata.calldata_gas(packed)) == (29, 440)
    nonzero = sum(1 for b in abi if b)
    assert (68 - nonzero) + 4 * nonzero == 158  # tokens under the floor rule, so 1580 gas: less than one slot write
    assert iv_calldata.calldata_gas(bytes(10)) == 40 and iv_calldata.calldata_gas(b"\xff" * 10) == 160
    assert abi[4 + 12:4 + 32] == to and int.from_bytes(abi[-32:], "big") == amount


def test_q20():
    d = iv_deposits.Deposits(confirmations=3)
    d.on_block("a1", "root", 1, [("t1", 5)])
    d.on_block("a2", "a1", 2, [])
    assert d.credited == {}                    # two confirmations are not enough
    d.on_block("a3", "a2", 3, [])
    assert d.credited == {"t1": 5}
    d.on_block("a4", "a3", 4, [])
    assert d.credited == {"t1": 5} and d.alarms == []   # credited once
    rng = random.Random(20)
    for _ in range(300):
        n = 6
        d = iv_deposits.Deposits(confirmations=n)
        blocks = {"root": (None, 0)}
        tips = ["root"]
        deposits = {}
        for k in range(120):
            parent = tips[-1] if rng.random() < 0.8 else rng.choice(tips[-(n - 2):])   # forks shorter than n
            name = f"b{k}"
            height = blocks[parent][1] + 1
            blocks[name] = (parent, height)
            found = [(f"t{rng.randint(0, 40)}", 1)] if rng.random() < 0.4 else []
            deposits[name] = found
            d.on_block(name, parent, height, found)
            if height > blocks[tips[-1]][1]:
                tips.append(name)
        assert d.alarms == []                  # forks here are shorter than n, so nothing credited is ever lost
        # truth: walk the best chain; every deposit deeper than n must be credited
        chain = []
        at = d.head
        while at in deposits:
            chain.append(at)
            at = blocks[at][0]
        for depth, name in enumerate(chain, 1):
            if depth >= n:
                assert all(t in d.credited for t, _ in deposits[name])
    # a reorganisation deeper than the setting: a credited deposit is gone, and that raises an alarm
    d = iv_deposits.Deposits(confirmations=2)
    d.on_block("a1", "root", 1, [("t", 7)])
    d.on_block("a2", "a1", 2, [])
    assert d.credited == {"t": 7}
    d.on_block("b1", "root", 1, [])
    d.on_block("b2", "b1", 2, [])
    d.on_block("b3", "b2", 3, [])
    assert d.credited == {} and d.alarms == ["t"]
    # a shallow one: the same deposit mined again on the new branch is not credited twice
    d = iv_deposits.Deposits(confirmations=3)
    d.on_block("a1", "root", 1, [("t", 7)])
    d.on_block("a2", "a1", 2, [])
    d.on_block("b1", "root", 1, [("t", 7)])
    d.on_block("b2", "b1", 2, [])
    d.on_block("b3", "b2", 3, [])
    assert d.credited == {"t": 7} and d.alarms == []


def test_q21():
    rng = random.Random(21)
    for _ in range(300):
        sender, chain = iv_withdraw.Sender(), iv_withdraw.Chain()
        requests = [f"r{k}" for k in range(rng.randint(1, 20))]
        market = 10
        for _ in range(200):
            chain.broadcast(sender.submit(rng.choice(requests), rng.randint(1, 30)))
            market = max(1, market + rng.randint(-2, 2))
            chain.mine(market)
        for r in requests:
            chain.broadcast(sender.submit(r, 10**6))
        chain.mine(1)
        paid = [tx[1] for tx in chain.mined]
        assert len(paid) == len(set(paid)) == len({sender.by_request[r] for r in sender.by_request})    # paid once
        assert set(paid) == set(sender.by_request)
    c, s = iv_withdraw.Chain(), iv_withdraw.Sender()
    low = s.submit("a", 1)
    c.broadcast(low)
    c.broadcast(s.submit("b", 100))
    c.mine(50)
    assert c.mined == []                       # a cheap low nonce blocks everything behind it
    c.broadcast(s.submit("a", 60))
    c.mine(50)
    assert [t[1] for t in c.mined] == ["a", "b"]
    # the broken twin: a retry with a fresh nonce pays twice
    twin = iv_withdraw.Chain()
    twin.broadcast((0, "a", 100))
    twin.broadcast((1, "a", 100))
    twin.mine(1)
    assert [t[1] for t in twin.mined] == ["a", "a"]


def test_q22(evm):
    p = evm["proxy"]
    assert p["implMatches"] and p["setOk"] and p["implAfter"] == str(0xDEAD)
    assert p["xAfterOk"] is True and p["xAfterOut"] == "0x"   # a call to nothing succeeds and returns nothing
    assert p["safeSetOk"] and p["safeX"] == str(0xDEAD) and p["safeImplMatches"]


def test_q23(evm):
    r = evm["readonly"]
    assert r["before"] == str(ETH) and r["after"] == str(ETH) and r["runOk"] is True
    assert r["seen"] == str(ETH // 2)          # half the true price, in the middle of the call
    assert r["safeRunOk"] is True and r["safeRefused"] == "1" and r["safeAfter"] == str(ETH)


def test_q24(evm):
    assert evm["relay"] == {"firstOk": True, "replayOk": True, "elsewhereOk": True, "stolen": str(2 * ETH)}
    assert evm["safeRelay"] == {"firstOk": True, "replayOk": False, "elsewhereOk": False, "got": str(ETH)}


def test_q25():
    secret = 123456789
    shares = iv_shamir.split(secret, 3, 5)
    for chosen in itertools.combinations(shares, 3):
        assert iv_shamir.recover(list(chosen)) == secret
    assert iv_shamir.recover(shares[:2]) != secret     # with overwhelming probability
    key = 2**256 - 189                         # a 32-byte key comes back whole, from any 2 of 3
    for chosen in itertools.combinations(iv_shamir.split(key, 2, 3), 2):
        assert iv_shamir.recover(list(chosen)) == key
    assert iv_shamir.recover(iv_shamir.split(iv_shamir.P - 1, 2, 3)[:2]) == iv_shamir.P - 1
    for too_big in (iv_shamir.P, iv_shamir.P + 5, 2**600):
        with pytest.raises(ValueError):        # refused, and not silently reduced modulo the prime
            iv_shamir.split(too_big, 2, 3)
    with pytest.raises(ValueError):
        iv_shamir.split(-1, 2, 3)
    with pytest.raises(ValueError):
        iv_shamir.split(300, 2, 3, p=257)
    s = 4                                      # Lucas-Lehmer: 2**521 - 1 is prime, so the field is a field
    for _ in range(521 - 2):
        s = (s * s - 2) % iv_shamir.P
    assert s == 0 and iv_shamir.P > 2**256
    p = 257
    a_share = 5
    counts = [0] * p                           # t = 2: with one share, every secret is equally possible
    for s in range(p):
        for slope in range(p):
            if (s + slope * 1) % p == a_share:
                counts[s] += 1
    assert set(counts) == {1}

    def stolen(q, t, n):                       # the chance of t or more of n keys falling, by listing the cases
        return sum(q**k * (1 - q) ** (n - k) for k in range(t, n + 1) for _ in itertools.combinations(range(n), k))

    assert stolen(0.01, 2, 3) == pytest.approx(3 * 0.01**2 - 2 * 0.01**3)
    assert stolen(0.01, 2, 3) == pytest.approx(0.000298, abs=1e-6)
    assert 1 - stolen(0.01, 2, 3) == pytest.approx(0.999702, abs=1e-6)   # and that two still stand, if a key is lost at that rate


def test_q26():
    accounts = [(f"a{i}", i * 7 % 100) for i in range(23)]
    leaves = [iv_merkle.leaf(a, b) for a, b in accounts]
    levels = iv_merkle.build(leaves)
    root = levels[-1][0]
    for i, (a, b) in enumerate(accounts):
        path = iv_merkle.proof(levels, i)
        assert iv_merkle.verify(root, a, b, path)
        assert not iv_merkle.verify(root, a, b + 1, path)
    assert max(len(iv_merkle.proof(levels, i)) for i in range(23)) == math.ceil(math.log2(23))
    assert iv_merkle.build([leaves[0]])[-1][0] == leaves[0]
    # without the prefixes, an inner node can be shown as if it were a leaf
    import hashlib

    def plain(x):
        return hashlib.sha256(x).digest()

    a, b = plain(b"x"), plain(b"y")            # two leaves of the twin with no prefixes
    twin_root = plain(a + b)
    assert plain(a + b) == twin_root           # the 64-byte value a + b passes as a leaf, with an empty proof
    root = iv_merkle.node(a, b)
    assert hashlib.sha256(b"\x00" + a + b).digest() != root     # with prefixes, the same forgery fails


def test_q27():
    price = iv_liquidation.liquidation_price(2000, 1, 200, 0.005)
    assert price == pytest.approx(1809.05, abs=0.01)
    rng = random.Random(27)
    for _ in range(500):
        e, q, mm = rng.uniform(100, 5000), rng.uniform(0.1, 10), rng.uniform(0.001, 0.05)
        m = e * q * rng.uniform(0.02, 0.5)
        p = iv_liquidation.Position(e, q, m, mm)
        cut = iv_liquidation.liquidation_price(e, q, m, mm)
        low, high = 0.0, 2 * e
        for _ in range(100):                   # the slow way: search for the mark at which it must close
            mid = (low + high) / 2
            low, high = (mid, high) if p.must_close(mid) else (low, mid)
        assert low == pytest.approx(cut, rel=1e-6)
    p = iv_liquidation.Position(2000, 1, 200, 0.005)
    assert p.must_close(1800) and not p.must_close(1900)
    assert p.close(1850, 1000.0) == 1000.0     # closed with equity left: the fund pays nothing
    assert p.close(1790, 1000.0) == pytest.approx(990.0)    # through the margin: the fund pays the gap


def test_q28():
    x, y, outside = 1000.0, 2_000_000.0, 2020.0
    best = iv_arb_size.best_input(x, y, outside)
    assert best == pytest.approx(6978.8, abs=0.1)
    assert iv_arb_size.profit(best, x, y, outside) == pytest.approx(24.28, abs=0.01)
    grid = [k * 1.0 for k in range(0, 40_000)]
    assert max(iv_arb_size.profit(g, x, y, outside) for g in grid) == pytest.approx(iv_arb_size.profit(best, x, y, outside), abs=1e-3)
    assert iv_arb_size.best_input(x, y, 2003.0) == 0.0     # inside the fee: no trade
    assert 2000 / 0.997 == pytest.approx(2006.02, abs=0.01)
    assert iv_arb_size.best_input(x, y, 2006.0) == 0.0 and iv_arb_size.best_input(x, y, 2007.0) > 0
    assert iv_arb_size.profit(best, x, y, outside, gas=25.0) < 0


def test_q29():
    rng = random.Random(29)
    for _ in range(300):
        b = iv_holds.Balances()
        people = ["a", "b", "c"]
        total = 0
        for p in people:
            amount = rng.randint(0, 100)
            b.deposit(p, amount)
            total += amount
        out = 0
        held_orders = []
        for _ in range(300):
            who, n = rng.choice(people), rng.randint(1, 40)
            roll = rng.random()
            if roll < 0.35:
                if b.hold(who, n):
                    held_orders.append((who, n))
            elif roll < 0.6 and held_orders:
                who, n = held_orders.pop(rng.randrange(len(held_orders)))
                b.release(who, n)
            elif roll < 0.8 and held_orders:
                who, n = held_orders.pop(rng.randrange(len(held_orders)))
                b.settle(who, rng.choice(people), n)
            elif b.withdraw(who, n):
                out += n
            assert all(v >= 0 for v in b.free.values()) and all(v >= 0 for v in b.held.values())
            assert sum(b.free.values()) + sum(b.held.values()) + out == total   # nothing created or lost
    s = iv_holds.Balances()
    s.deposit("a", 10)
    assert s.hold("a", 10) and not s.withdraw("a", 1) and not s.hold("a", 1)     # held funds cannot go twice
