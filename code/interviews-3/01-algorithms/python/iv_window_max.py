from collections import deque


def window_max(xs, k):
    out = []
    q = deque()                       # positions, with their values strictly decreasing
    for i, x in enumerate(xs):
        while q and xs[q[-1]] <= x:   # x outlives and beats these: never a maximum again
            q.pop()
        q.append(i)
        if q[0] <= i - k:             # the front has slid out of the window
            q.popleft()
        if i >= k - 1:
            out.append(xs[q[0]])
    return out


def window_min(xs, k):
    return [-v for v in window_max([-x for x in xs], k)]


def window_range(xs, k):
    return [a - b for a, b in zip(window_max(xs, k), window_min(xs, k), strict=True)]


def time_window_max(events, width):
    """events: (time, value) in time order. The maximum over the half-open span (t - width, t]."""
    out = []
    q = deque()
    for t, x in events:
        while q and q[-1][1] <= x:
            q.pop()
        q.append((t, x))
        while q[0][0] <= t - width:
            q.popleft()
        out.append(q[0][1])
    return out
