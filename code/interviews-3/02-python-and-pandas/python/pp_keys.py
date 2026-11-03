d = {(1, 2): "tuple"}
print(d[(1, 2)])
for key in ([1, 2], (1, [2]), frozenset([1, 2])):
    try:
        print(d.get(key, "absent"))
    except TypeError as e:
        print("TypeError:", e)
