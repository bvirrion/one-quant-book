"""Book 18, chapter 25: exhaustive interleaving explorers and the chapter's systems arithmetic.

The explorers enumerate every interleaving of small programs under sequential consistency (each thread's
operations in program order, one global order of memory operations). They answer "which outcomes are
possible" exactly for that model; weaker models (x86 TSO, C++ relaxed atomics) allow more, as stated in the text.
"""
from functools import cache


def counter_final_values(iterations: int, threads: int = 2):
    """Final values of a shared counter when each thread runs `iterations` times: r = x; x = r + 1."""
    finals = set()

    @cache
    def go(state):
        # state: tuple of (done_iterations, phase, register) per thread, then x
        *ts, x = state
        moved = False
        for i, (k, phase, r) in enumerate(ts):
            if k == iterations:
                continue
            moved = True
            new = list(ts)
            if phase == 0:
                new[i] = (k, 1, x)  # load
                go(tuple(new) + (x,))
            else:
                new[i] = (k + 1, 0, 0)  # store r + 1
                go(tuple(new) + (r + 1,))
        if not moved:
            finals.add(x)

    go(tuple((0, 0, 0) for _ in range(threads)) + (0,))
    return finals


def sc_outcomes(t1, t2):
    """All (register values) outcomes of two straight-line threads under sequential consistency.
    Each operation is ('st', var, value) or ('ld', var, reg)."""
    out = set()

    def go(i, j, mem, regs):
        if i == len(t1) and j == len(t2):
            out.add(tuple(sorted(regs.items())))
            return
        for which, ops, k in ((0, t1, i), (1, t2, j)):
            if k == len(ops):
                continue
            op, var, arg = ops[k]
            m, r = dict(mem), dict(regs)
            if op == "st":
                m[var] = arg
            else:
                r[arg] = m.get(var, 0)
            go(i + (which == 0), j + (which == 1), m, r)

    go(0, 0, {}, {})
    return out


STORE_BUFFERING = ([("st", "x", 1), ("ld", "y", "r1")], [("st", "y", 1), ("ld", "x", "r2")])
MESSAGE_PASSING = ([("st", "data", 1), ("st", "flag", 1)], [("ld", "flag", "r1"), ("ld", "data", "r2")])


def page_table_levels(va_bits: int = 48, page_bytes: int = 4096, entry_bytes: int = 8):
    """Levels of a radix page table whose nodes are one page of entries."""
    offset = page_bytes.bit_length() - 1
    per_level = (page_bytes // entry_bytes).bit_length() - 1
    return -(-(va_bits - offset) // per_level), per_level, offset


def tlb_reach(entries: int, page_bytes: int) -> int:
    return entries * page_bytes


def gaps(seqs):
    """Missing sequence-number ranges in a stream that should be consecutive; duplicates and late
    arrivals are ignored. Returns a list of (first_missing, last_missing)."""
    expected, out, seen_late = None, [], set()
    for s in seqs:
        if expected is None:
            expected = s + 1
            continue
        if s == expected:
            expected += 1
        elif s > expected:
            out.append((expected, s - 1))
            expected = s + 1
        else:
            seen_late.add(s)
    # late arrivals fill earlier gaps
    filled = []
    for a, b in out:
        cur = a
        for x in range(a, b + 1):
            if x in seen_late:
                if cur <= x - 1:
                    filled.append((cur, x - 1))
                cur = x + 1
        if cur <= b:
            filled.append((cur, b))
    return filled
