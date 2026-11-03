def max_profit_k(prices, k):
    if k >= len(prices) // 2:         # enough round trips to take every rise
        return sum(max(0, b - a) for a, b in zip(prices, prices[1:], strict=False))
    flat = [0] * (k + 1)              # flat[j]: best wealth after j completed round trips
    long = [float("-inf")] * (k + 1)  # long[j]: holding, on the way to round trip j
    for p in prices:
        for j in range(1, k + 1):
            long[j] = max(long[j], flat[j - 1] - p)
            flat[j] = max(flat[j], long[j] + p)
    return flat[k]
