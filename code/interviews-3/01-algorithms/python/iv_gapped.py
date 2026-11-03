from collections import deque


def best_gapped(xs, k):
    """Largest sum of a non-empty subsequence whose neighbouring picks are at most k apart."""
    dp = [0] * len(xs)                # dp[i]: the best sum of picks ending at i
    q = deque()                       # positions with dp strictly decreasing
    for i, x in enumerate(xs):
        if q and q[0] < i - k:
            q.popleft()
        dp[i] = x + max(0, dp[q[0]] if q else 0)
        while q and dp[q[-1]] <= dp[i]:
            q.pop()
        q.append(i)
    return max(dp)
