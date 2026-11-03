def is_power_of_two(x):
    return x > 0 and x & (x - 1) == 0


def count_set_bits(x):
    n = 0
    while x:
        x &= x - 1                    # clears the lowest set bit
        n += 1
    return n


def next_power_of_two(x):             # the smallest power of two >= x, for x >= 1
    return 1 << (x - 1).bit_length()
