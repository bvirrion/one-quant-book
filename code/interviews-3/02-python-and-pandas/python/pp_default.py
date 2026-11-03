# ruff: noqa: B006
def add(x, items=[]):
    items.append(x)
    return items


print(add(1))
print(add(2))
print(add(3, []))
print(add(4))
