from bisect import bisect_right


def best_total(jobs):
    """jobs: (start, end, profit); a job may start when another ends."""
    jobs = sorted(jobs, key=lambda j: j[1])
    ends = [j[1] for j in jobs]
    best = [0] * (len(jobs) + 1)      # best[i]: using the first i jobs by end time
    for i, (start, _, profit) in enumerate(jobs):
        compatible = bisect_right(ends, start, 0, i)
        best[i + 1] = max(best[i], best[compatible] + profit)
    return best[-1]
