scores = {"AAA": 1.0, "BBB": 1.0, "CCC": 1.0, "DDD": 1.0}
weights = {"AAA": 1e16, "BBB": 1.0, "CCC": -1e16, "DDD": 0.0}
symbols = set(scores)
print(max(symbols, key=scores.get))
print(sum(weights[s] for s in symbols))
