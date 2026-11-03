from collections import deque


def run_order(n, edges):
    """edges: (a, b) means a before b. Returns an order, or None on a cycle."""
    after = [[] for _ in range(n)]
    waiting = [0] * n
    for a, b in edges:
        after[a].append(b)
        waiting[b] += 1
    ready = deque(i for i in range(n) if waiting[i] == 0)
    order = []
    while ready:
        a = ready.popleft()
        order.append(a)
        for b in after[a]:
            waiting[b] -= 1
            if waiting[b] == 0:
                ready.append(b)
    return order if len(order) == n else None


# Not printed: the follow-up.
def finish_time(durations, edges):
    order = run_order(len(durations), edges)
    done = [0] * len(durations)
    start = [0] * len(durations)
    after = [[] for _ in durations]
    for a, b in edges:
        after[a].append(b)
    for a in order:
        done[a] = start[a] + durations[a]
        for b in after[a]:
            start[b] = max(start[b], done[a])
    return max(done, default=0)
