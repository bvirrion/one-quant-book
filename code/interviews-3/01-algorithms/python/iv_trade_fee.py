def max_profit_with_fee(prices, fee):
    flat, holding = 0, float("-inf")  # the best wealth so far, not holding and holding
    for p in prices:
        holding = max(holding, flat - p)
        flat = max(flat, holding + p - fee)
    return flat
