import random


def build(weights):
    n, total = len(weights), sum(weights)
    scaled = [w * n / total for w in weights]
    prob, other = [1] * n, list(range(n))
    small = [i for i, s in enumerate(scaled) if s < 1]
    large = [i for i, s in enumerate(scaled) if s > 1]
    while small and large:
        a, b = small.pop(), large.pop()
        prob[a], other[a] = scaled[a], b     # slot a: item a with prob[a], else item b
        scaled[b] -= 1 - scaled[a]
        (small if scaled[b] < 1 else large if scaled[b] > 1 else []).append(b)
    return prob, other


def draw(prob, other, rng=random):
    i = rng.randrange(len(prob))
    return i if rng.random() < prob[i] else other[i]
