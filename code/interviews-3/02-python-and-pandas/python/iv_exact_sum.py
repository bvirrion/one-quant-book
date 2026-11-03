def neumaier(xs):
    total = lost = 0.0
    for x in xs:
        t = total + x
        if abs(total) >= abs(x):
            lost += (total - t) + x   # the low bits of x that the addition dropped
        else:
            lost += (x - t) + total
        total = t
    return total + lost


# Not printed: plain Kahan, for the wrong answer.
def kahan(xs):
    total = c = 0.0
    for x in xs:
        y = x - c
        t = total + y
        c = (t - total) - y
        total = t
    return total
