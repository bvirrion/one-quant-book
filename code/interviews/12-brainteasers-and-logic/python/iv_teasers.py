"""Book 18, chapter 12: every brainteaser answer by exhaustive search or direct construction."""
import itertools
import random
from functools import cache


def token_game(red: int, blue: int, rng: random.Random) -> str:
    """Take two tokens at random: same colour -> put back a red; different -> put back a blue."""
    bag = ["r"] * red + ["b"] * blue
    while len(bag) > 1:
        rng.shuffle(bag)
        a, b = bag.pop(), bag.pop()
        bag.append("r" if a == b else "b")
    return bag[0]


def losing_positions(n_max: int, moves) -> list:
    """Positions (tokens left, player to move, last to take wins) from which the mover loses."""
    win = [False] * (n_max + 1)
    for n in range(1, n_max + 1):
        win[n] = any(m <= n and not win[n - m] for m in moves)
    return [n for n in range(n_max + 1) if not win[n]]


def hat_line(colours, k: int) -> int:
    """Line of hats with k colours; person 0 sees everyone else and announces sum mod k; each later person
    deduces their own. Returns the number of correct guesses."""
    n = len(colours)
    announce = sum(colours[1:]) % k
    correct = int(announce == colours[0])
    heard = [announce]
    for i in range(1, n):
        others = sum(colours[j] for j in range(i + 1, n))
        told = sum(heard[1:])  # colours already announced correctly by persons 1..i-1
        guess = (announce - others - told) % k
        correct += guess == colours[i]
        heard.append(guess)
    return correct


def fake_bag(weights_deficit: float, per_coin: float = 0.1) -> int:
    """Take i coins from bag i (1..n); the deficit in grams identifies the bag of light coins."""
    return round(weights_deficit / per_coin)


def divide_coins(n: int, coins: int = 100):
    """Seniority division: the most senior remaining proposes; it passes with at least half of the votes
    (ties pass; the proposer votes for it); a rejected proposer leaves with nothing. Voters accept only if
    strictly better off than after a rejection. Returns allocations indexed from the most senior."""
    alloc = {1: [coins]}
    for m in range(2, n + 1):
        nxt = alloc[m - 1]  # allocation among the m-1 juniors if the proposal fails
        need = (m + 1) // 2 - 1  # extra votes needed besides the proposer's
        cost = sorted(range(m - 1), key=lambda j: nxt[j])
        chosen = cost[:need]
        new = [0] * m
        for j in chosen:
            new[j + 1] = nxt[j] + 1
        new[0] = coins - sum(new)
        alloc[m] = new
    return alloc[n]


def announcement_rounds(badges):
    """Muddy-children dynamics: 'at least one is red' is announced; each round, a person who knows their own
    colour steps forward. Returns (round, set of people who step forward first)."""
    n = len(badges)
    worlds = [w for w in itertools.product([0, 1], repeat=n) if any(w)]
    for rnd in range(1, n + 1):
        knowers = set()
        for i in range(n):
            consistent = {w[i] for w in worlds if all(w[j] == badges[j] for j in range(n) if j != i)}
            if len(consistent) == 1:
                knowers.add(i)
        if knowers:
            return rnd, knowers
        # nobody stepped forward: eliminate worlds in which someone would have known
        keep = []
        for w in worlds:
            someone = False
            for i in range(n):
                cons = {v[i] for v in worlds if all(v[j] == w[j] for j in range(n) if j != i)}
                if len(cons) == 1:
                    someone = True
                    break
            if not someone:
                keep.append(w)
        worlds = keep
    return None


def hat_circle_value(strategy, n: int = 3):
    """Evaluate a strategy for the simultaneous hat game: strategy(i, view) returns 0 (red), 1 (blue) or
    2 (pass), where view is the tuple of the other players' colours. Returns (winning share, total correct
    guesses, total wrong guesses) over the 2^n equally likely configurations."""
    wins = right = wrong = 0
    for c in itertools.product([0, 1], repeat=n):
        acts = [strategy(i, tuple(c[j] for j in range(n) if j != i)) for i in range(n)]
        r = sum(a == c[i] for i, a in enumerate(acts))
        w = sum(a != 2 and a != c[i] for i, a in enumerate(acts))
        right, wrong = right + r, wrong + w
        wins += r > 0 and w == 0
    return wins / 2**n, right, wrong


def majority_rule(i, view):
    """Three players: if the two others match, guess the opposite colour; otherwise pass."""
    return 1 - view[0] if view[0] == view[1] else 2


def hamming_hat(n_bits: int = 7) -> float:
    """Hamming(7,4) strategy: a player guesses the colour that would make the configuration a non-codeword
    whenever the other colour makes it a codeword; otherwise passes."""
    def syndrome(v):
        s = 0
        for i, b in enumerate(v, start=1):
            if b:
                s ^= i
        return s

    wins = 0
    for c in itertools.product([0, 1], repeat=n_bits):
        acts = []
        for i in range(n_bits):
            v0 = list(c)
            v0[i] = 0
            v1 = list(c)
            v1[i] = 1
            if syndrome(v0) == 0:
                acts.append(1)
            elif syndrome(v1) == 0:
                acts.append(0)
            else:
                acts.append(2)
        guessed = [a != 2 for a in acts]
        ok = all(a == 2 or a == c[i] for i, a in enumerate(acts))
        wins += any(guessed) and ok
    return wins / 2**n_bits


def replace_rule_final(values) -> int:
    """Replace any a, b by a + b + ab: the product of (1 + x) is invariant; the final number is that product - 1."""
    p = 1
    for v in values:
        p *= 1 + v
    return p - 1


def replace_rule_simulate(values, rng: random.Random) -> int:
    xs = list(values)
    while len(xs) > 1:
        rng.shuffle(xs)
        a, b = xs.pop(), xs.pop()
        xs.append(a + b + a * b)
    return xs[0]


def zero_block_exists(values, m: int) -> bool:
    """Is there a non-empty block of consecutive values whose sum is divisible by m?"""
    seen = {0}
    s = 0
    for v in values:
        s = (s + v) % m
        if s in seen:
            return True
        seen.add(s)
    return False


@cache
def chomp_first_player_wins(state) -> bool:
    """Chomp on a rectangular bar: state is a tuple of non-increasing row lengths; the top-left square is
    poisoned (taking it loses). A player to move wins if some move leads to a losing state for the other."""
    moves = []
    for r, length in enumerate(state):
        for c in range(length):
            if r == 0 and c == 0:
                continue
            new = tuple(min(x, c) if i >= r else x for i, x in enumerate(state))
            new = tuple(x for x in new if x > 0)
            moves.append(new)
    return any(not chomp_first_player_wins(m) for m in moves)
