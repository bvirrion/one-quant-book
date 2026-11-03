nan = float("nan")
print(nan == nan, nan in [nan], float("nan") in [nan])
print(max(nan, 1.0), max(1.0, nan))
print(sorted([2.0, nan, 1.0]))
