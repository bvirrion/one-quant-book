from collections import deque


def shortest_at_least(xs, target):
    """Length of the shortest contiguous span with sum >= target > 0, or None."""
    prefix = [0]
    for x in xs:
        prefix.append(prefix[-1] + x)
    best = None
    q = deque()                       # candidate starts, prefix values strictly increasing
    for j, s in enumerate(prefix):
        while q and s - prefix[q[0]] >= target:
            i = q.popleft()           # no later end can beat this start's shortest span
            if best is None or j - i < best:
                best = j - i
        while q and prefix[q[-1]] >= s:
            q.pop()                   # j is later and no higher: it dominates this start
        q.append(j)
    return best
