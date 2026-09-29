pricers = [lambda x: x * k for k in range(3)]  # noqa: B023 -- the bug the question is about
print([p(10) for p in pricers])
fixed = [lambda x, k=k: x * k for k in range(3)]
print([p(10) for p in fixed])
