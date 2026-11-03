"""Simple sequence rules, used to show which rule fits a printed sequence and which do not."""
from fractions import Fraction as F


def differences(seq):
    return [b - a for a, b in zip(seq, seq[1:], strict=False)]


def ratios(seq):
    return [F(b, a) for a, b in zip(seq, seq[1:], strict=False)]


def constant(values):
    return len(set(values)) == 1


def poly_next(seq):
    """The next term of the unique polynomial of lowest degree through the terms: extend the difference table."""
    rows = [list(seq)]
    while len(rows[-1]) > 1:
        rows.append(differences(rows[-1]))
    value = 0
    for row in reversed(rows):
        value += row[-1]
    return value


def fits_simple_rule(seq):
    """True if the sequence is arithmetic, geometric or Fibonacci-type, or has constant second differences."""
    d = differences(seq)
    if constant(d) or (len(seq) > 3 and constant(differences(d))):
        return True
    if all(a != 0 for a in seq) and constant(ratios(seq)):
        return True
    return all(c == a + b for a, b, c in zip(seq, seq[1:], seq[2:], strict=False))


def digit_sum(n):
    return sum(map(int, str(n)))


def digit_product(n):
    out = 1
    for ch in str(n):
        if ch != "0":
            out *= int(ch)
    return out
