def two_singles(ids):
    both = 0
    for x in ids:
        both ^= x                     # the pairs cancel, leaving a ^ b
    low = both & -both                # a bit on which a and b differ
    a = 0
    for x in ids:
        if x & low:
            a ^= x                    # the pairs cancel in this half too
    return a, both ^ a


# Not printed: the follow-up.
def single_among_triples(ids, bits=32):
    out = 0
    for b in range(bits):
        if sum((x >> b) & 1 for x in ids) % 3:
            out |= 1 << b
    return out
