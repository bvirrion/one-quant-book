# ruff: noqa: B905
z = zip([1, 2], [3, 4])
print(list(z))
print(list(z))
g = (x * x for x in range(3))
print(sum(g), sum(g))
r = range(3)
print(sum(r), sum(r))
