"""Shamir's scheme over a prime field: t of n shares give the secret, t - 1 say nothing."""
import secrets

P = 2**521 - 1                               # a prime well above a 32-byte key


def split(secret, t, n, p=P, rand=secrets.randbelow):
    if not 0 <= secret < p:
        raise ValueError("the field must be larger than the secret")
    coefficients = [secret] + [rand(p) for _ in range(t - 1)]

    def poly(x):
        return sum(c * pow(x, k, p) for k, c in enumerate(coefficients)) % p

    return [(x, poly(x)) for x in range(1, n + 1)]


def recover(shares, p=P):
    """Lagrange interpolation at x = 0."""
    total = 0
    for i, (xi, yi) in enumerate(shares):
        top, bottom = 1, 1
        for j, (xj, _) in enumerate(shares):
            if i != j:
                top = top * -xj % p
                bottom = bottom * (xi - xj) % p
        total = (total + yi * top * pow(bottom, -1, p)) % p
    return total
