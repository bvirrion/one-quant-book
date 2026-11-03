import random


def shuffle(xs, rng=random):
    for i in range(len(xs) - 1, 0, -1):
        j = rng.randrange(i + 1)      # from the part not yet fixed, i included
        xs[i], xs[j] = xs[j], xs[i]
