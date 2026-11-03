from collections import Counter


def count_sum(xs, target):
    seen = Counter({0: 1})        # the empty prefix
    prefix = count = 0
    for x in xs:
        prefix += x
        count += seen[prefix - target]
        seen[prefix] += 1         # after the lookup, so an empty span never counts
    return count


def count_divisible(xs, m):
    """How many contiguous spans have a sum divisible by m."""
    seen = Counter({0: 1})
    prefix = count = 0
    for x in xs:
        prefix = (prefix + x) % m
        count += seen[prefix]
        seen[prefix] += 1
    return count
