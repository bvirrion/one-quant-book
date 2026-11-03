from collections import Counter


def longest_k_distinct(tape, k):
    count = Counter()
    best = left = 0
    for right, s in enumerate(tape):
        count[s] += 1
        while len(count) > k:
            count[tape[left]] -= 1
            if not count[tape[left]]:
                del count[tape[left]]
            left += 1
        best = max(best, right - left + 1)
    return best


# Not printed: the follow-up.
def count_at_most(tape, k):
    if k <= 0:
        return 0
    count = Counter()
    total = left = 0
    for right, s in enumerate(tape):
        count[s] += 1
        while len(count) > k:
            count[tape[left]] -= 1
            if not count[tape[left]]:
                del count[tape[left]]
            left += 1
        total += right - left + 1
    return total


def count_exactly(tape, k):
    return count_at_most(tape, k) - count_at_most(tape, k - 1)
