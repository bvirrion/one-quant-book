def is_bst(node, low=None, high=None):
    """node: (key, left, right) or None. Every key must lie strictly between its limits."""
    stack = [(node, low, high)]
    while stack:
        n, lo, hi = stack.pop()
        if n is None:
            continue
        key, left, right = n
        if (lo is not None and key <= lo) or (hi is not None and key >= hi):
            return False
        stack.append((left, lo, key))
        stack.append((right, key, hi))
    return True


# Not printed: the wrong answer and the second route.
def children_only(node):
    if node is None:
        return True
    key, left, right = node
    if left and left[0] >= key:
        return False
    if right and right[0] <= key:
        return False
    return children_only(left) and children_only(right)


def in_order(node):
    if node is None:
        return []
    return in_order(node[1]) + [node[0]] + in_order(node[2])
