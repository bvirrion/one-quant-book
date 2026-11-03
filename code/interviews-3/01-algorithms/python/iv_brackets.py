def balanced(s):
    closes = {")": "(", "]": "[", "}": "{"}
    stack = []
    for c in s:
        if c in closes:
            if not stack or stack.pop() != closes[c]:
                return False
        else:
            stack.append(c)
    return not stack


# Not printed: the follow-up and the classic wrong answer.
def longest_valid(s):
    best = 0
    stack = [-1]  # the position just before the current valid stretch
    for i, c in enumerate(s):
        if c == "(":
            stack.append(i)
        else:
            stack.pop()
            if stack:
                best = max(best, i - stack[-1])
            else:
                stack.append(i)
    return best


def counters_only(s):
    counts = {"(": 0, "[": 0, "{": 0}
    closes = {")": "(", "]": "[", "}": "{"}
    for c in s:
        if c in closes:
            counts[closes[c]] -= 1
            if counts[closes[c]] < 0:
                return False
        else:
            counts[c] += 1
    return not any(counts.values())
