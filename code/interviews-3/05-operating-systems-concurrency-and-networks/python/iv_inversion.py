"""One CPU, strict priorities, by ticks. A task is (priority, arrival, program), a program
("cpu", n) and ("lock", n) steps, the second holding the lock n ticks. Larger is higher."""


def simulate(tasks, inherit=False):
    left = [[list(step) for step in prog] for _, _, prog in tasks]
    done, owner, now = [None] * len(tasks), None, 0
    while any(d is None for d in done):
        ready, waiters = [], []
        for i, (prio, arrival, _) in enumerate(tasks):
            if done[i] is not None or arrival > now:
                continue
            if left[i][0][0] == "lock" and owner not in (None, i):
                waiters.append(prio)
            else:
                ready.append(i)
        effective = {i: tasks[i][0] for i in ready}
        if inherit and owner in effective and waiters:
            effective[owner] = max(effective[owner], *waiters)   # at its waiter's priority
        now += 1
        if not ready:
            continue
        i = max(ready, key=lambda k: effective[k])
        step = left[i][0]
        if step[0] == "lock":
            owner = i
        step[1] -= 1
        if step[1] == 0:
            if step[0] == "lock":
                owner = None
            left[i].pop(0)
            if not left[i]:
                done[i] = now
    return done
