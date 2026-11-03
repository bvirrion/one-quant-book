def days_until_higher(prices):
    out = [0] * len(prices)
    waiting = []                      # days with no higher price yet
    for i, p in enumerate(prices):
        while waiting and prices[waiting[-1]] < p:
            j = waiting.pop()
            out[j] = i - j
        waiting.append(i)
    return out


# Not printed: the follow-up.
def span(prices):
    out = []
    stack = []
    for i, p in enumerate(prices):
        while stack and prices[stack[-1]] <= p:
            stack.pop()
        out.append(i - stack[-1] if stack else i + 1)
        stack.append(i)
    return out
