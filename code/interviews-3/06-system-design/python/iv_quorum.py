"""Synchronous replication: a commit waits for `needed` acks, the writer's own included."""


def commit_ms(rtts, needed):
    """rtts lists the round trip to each replica, 0 for the writer itself."""
    return sorted(rtts)[needed - 1]


def majority(n):
    return n // 2 + 1
