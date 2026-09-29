def add_fill(fill, fills=[]):  # noqa: B006 -- the bug the question is about
    fills.append(fill)
    return fills


print(add_fill(1))
print(add_fill(2))
print(add_fill(3, []))
