def sum_of_minimums(xs):
    total = 0
    stack = []                        # positions with strictly rising values
    for i, x in enumerate([*xs, float("-inf")]):
        while stack and xs[stack[-1]] >= x:
            j = stack.pop()
            left = stack[-1] if stack else -1
            total += xs[j] * (j - left) * (i - j)   # stretches where xs[j] is the minimum
        stack.append(i)
    return total
