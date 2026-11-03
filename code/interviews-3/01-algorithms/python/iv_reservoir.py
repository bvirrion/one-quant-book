def reservoir(stream, k, rng):
    sample = []
    for i, x in enumerate(stream):        # i items came before x
        if i < k:
            sample.append(x)
        else:
            j = rng.randrange(i + 1)      # uniform on 0..i, so P(j < k) = k / (i + 1)
            if j < k:
                sample[j] = x
    return sample


def weighted_key(rng, weight):
    """Keep the k largest keys u ** (1 / w). For k = 1, item i survives with probability w_i / W."""
    return rng.random() ** (1 / weight)
