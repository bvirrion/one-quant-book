def fewest_clips(sizes, n):
    inf = n + 1
    best = [0] + [inf] * n            # best[q]: fewest clips adding up to exactly q
    used = [0] * (n + 1)
    for q in range(1, n + 1):
        for s in sizes:
            if s <= q and best[q - s] + 1 < best[q]:
                best[q], used[q] = best[q - s] + 1, s
    if best[n] == inf:
        return None
    clips = []
    while n:
        clips.append(used[n])
        n -= used[n]
    return clips


# Not printed: the wrong answer and the follow-up.
def greedy(sizes, n):
    clips = []
    for s in sorted(sizes, reverse=True):
        while n >= s:
            clips.append(s)
            n -= s
    return clips if n == 0 else None


def ways(sizes, n):
    count = [1] + [0] * n
    for s in sizes:                   # one size at a time, so each combination counts once
        for q in range(s, n + 1):
            count[q] += count[q - s]
    return count[n]
