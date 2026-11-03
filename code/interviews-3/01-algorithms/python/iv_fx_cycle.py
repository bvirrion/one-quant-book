from math import log


def find_arbitrage(rates, eps=1e-9):
    """rates: {(a, b): units of b for one unit of a}. A cycle [c0, c1, ..., c0] or None."""
    nodes = sorted({c for pair in rates for c in pair})
    edges = [(a, b, -log(r)) for (a, b), r in rates.items()]
    dist = dict.fromkeys(nodes, 0.0)      # as if a hidden source reached every node at cost 0
    prev = {}
    changed = None
    for _ in nodes:                       # a change in round n can only come from a cycle
        changed = None
        for a, b, w in edges:
            if dist[a] + w < dist[b] - eps:
                dist[b] = dist[a] + w
                prev[b] = a
                changed = b
        if changed is None:
            break
    if changed is None:
        return None
    c = changed
    for _ in nodes:                       # n steps back must land on the cycle itself
        c = prev[c]
    cycle, x = [c], prev[c]
    while x != c:
        cycle.append(x)
        x = prev[x]
    cycle.append(c)
    return cycle[::-1]
