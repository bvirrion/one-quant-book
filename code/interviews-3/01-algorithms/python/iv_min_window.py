from collections import Counter


def smallest_window(tape, need):
    """(start, end) of the shortest stretch covering the multiset need, or None."""
    missing = Counter(need)
    short = len(need)                 # how many required items are still uncovered
    best, left = None, 0
    for right, s in enumerate(tape):
        if missing[s] > 0:
            short -= 1
        missing[s] -= 1
        while short == 0:
            if best is None or right - left < best[1] - best[0]:
                best = (left, right)
            missing[tape[left]] += 1
            if missing[tape[left]] > 0:
                short += 1
            left += 1
    return best
