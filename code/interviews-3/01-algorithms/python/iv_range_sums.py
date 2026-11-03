def count_in_range(xs, low, high):
    """Stretches of xs whose sum lies in [low, high], by merge sort over prefix sums."""
    prefix = [0]
    for x in xs:
        prefix.append(prefix[-1] + x)

    def go(a):                        # returns a sorted, and the count across its pairs
        if len(a) < 2:
            return a, 0
        left, c1 = go(a[: len(a) // 2])
        right, c2 = go(a[len(a) // 2 :])
        count, i, j = c1 + c2, 0, 0
        for p in left:                # right ends with sums in range, for this left end
            while i < len(right) and right[i] - p < low:
                i += 1
            while j < len(right) and right[j] - p <= high:
                j += 1
            count += j - i
        return sorted(left + right), count

    return go(prefix)[1]
