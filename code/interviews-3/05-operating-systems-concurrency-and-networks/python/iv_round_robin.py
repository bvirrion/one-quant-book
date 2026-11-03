"""Completion times under round robin, all tasks arriving at time 0 in the order given."""
from collections import deque


def round_robin(bursts, quantum):
    left = list(bursts)
    queue = deque(i for i, b in enumerate(bursts) if b > 0)
    done = [0] * len(bursts)
    now = 0
    while queue:
        i = queue.popleft()
        run = min(quantum, left[i])
        now += run
        left[i] -= run
        if left[i]:
            queue.append(i)
        else:
            done[i] = now
    return done
