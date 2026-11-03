def largest_rectangle(bars):
    best = 0
    stack = []                        # positions of rising bars still able to extend right
    for i, h in enumerate([*bars, 0]):
        while stack and bars[stack[-1]] >= h:
            height = bars[stack.pop()]
            left = stack[-1] + 1 if stack else 0
            best = max(best, height * (i - left))
        stack.append(i)
    return best
