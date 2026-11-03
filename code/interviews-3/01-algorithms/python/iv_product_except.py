def product_except_self(xs):
    out = [1] * len(xs)
    left = 1
    for i, x in enumerate(xs):
        out[i] = left                 # the product of everything before i
        left *= x
    right = 1
    for i in range(len(xs) - 1, -1, -1):
        out[i] *= right               # and of everything after i
        right *= xs[i]
    return out
