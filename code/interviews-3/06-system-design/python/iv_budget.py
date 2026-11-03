"""The exact distribution of a sum of independent stages, each a list of (value, prob)."""


def distribution_of_sum(stages):
    dist = {0: 1.0}
    for stage in stages:
        next_dist = {}
        for total, p in dist.items():
            for value, q in stage:
                next_dist[total + value] = next_dist.get(total + value, 0.0) + p * q
        dist = next_dist
    return dist


def percentile(dist, level):
    total = 0.0
    for value in sorted(dist):
        total += dist[value]
        if total >= level:
            return value
    return max(dist)
