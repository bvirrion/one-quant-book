def matches(text, pattern):
    """. matches any character, x* zero or more of x; the whole text must match."""
    n, m = len(text), len(pattern)
    ok = [[False] * (m + 1) for _ in range(n + 1)]
    ok[n][m] = True                   # ok[i][j]: text[i:] matches pattern[j:]
    for i in range(n, -1, -1):
        for j in range(m - 1, -1, -1):
            first = i < n and pattern[j] in (text[i], ".")
            if j + 1 < m and pattern[j + 1] == "*":
                ok[i][j] = ok[i][j + 2] or (first and ok[i + 1][j])
            else:
                ok[i][j] = first and ok[i + 1][j + 1]
    return ok[0][0]
