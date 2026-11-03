"""Finding a deadlock: who holds which lock, and who waits for which."""


def find_cycle(holder, waits):
    """holder: lock to thread; waits: thread to the lock it needs. Returns a cycle or None."""
    done = set()
    for start in waits:
        path, seen = [], {}
        t = start
        while t in waits and t not in done:
            if t in seen:
                return path[seen[t]:]
            seen[t] = len(path)
            path.append(t)
            t = holder.get(waits[t])
        done.update(path)
    return None
