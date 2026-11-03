"""A Merkle tree of (account, balance) leaves, with an inclusion proof for one of them."""
import hashlib


def leaf(account, balance):
    return hashlib.sha256(b"\x00" + f"{account}:{balance}".encode()).digest()


def node(a, b):
    return hashlib.sha256(b"\x01" + a + b).digest()


def build(leaves):
    """Returns the levels, leaves first. An odd node goes up unpaired."""
    levels = [leaves]
    while len(levels[-1]) > 1:
        row = levels[-1]
        levels.append([node(row[i], row[i + 1]) if i + 1 < len(row) else row[i]
                       for i in range(0, len(row), 2)])
    return levels


def proof(levels, index):
    path = []
    for row in levels[:-1]:
        sibling = index ^ 1
        if sibling < len(row):
            path.append((row[sibling], index % 2 == 0))
        index //= 2
    return path


def verify(root, account, balance, path):
    current = leaf(account, balance)
    for sibling, we_are_left in path:
        current = node(current, sibling) if we_are_left else node(sibling, current)
    return current == root
