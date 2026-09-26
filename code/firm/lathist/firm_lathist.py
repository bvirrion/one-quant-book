"""firm.lathist -- log-linear latency histogram (build of One Quant Book 13, chapter 5). Python reference of the
C++20 (cpp/firm_lathist.hpp) and Rust (rust/) twins, which reproduce data/fixture_*.csv exactly.

Values are non-negative integers (nanoseconds). With S sub-bucket bits (default 8):
    v < 2**S                       index v (exact)
    otherwise, shift = bitlen(v) - S, mantissa = v >> shift in [2**(S-1), 2**S):
                                   index 2**S + (shift - 1) * 2**(S-1) + (mantissa - 2**(S-1))
A bucket covers [mantissa << shift, (mantissa + 1) << shift): its width is at most 2**-(S-1) of any value in it
(0.78% for S = 8). Recording is a few shifts and an increment; the table has a fixed size (7,424 counts for S = 8 and
64-bit values), so recording never allocates.

Coordinated omission (Tene): a closed-loop tester sends the next request only after the previous reply, so a stall of
length L hides the L / interval requests that should have been sent meanwhile. `record_corrected(v, interval)` adds
the missing samples v - interval, v - 2 interval, ... while they exceed `interval` (as HdrHistogram's
recordValueWithExpectedInterval does).

API (stable):
    LatHist(sub_bits=8)
    .record(v, n=1) .record_corrected(v, interval) .merge(other)
    .count .min .max .mean() .quantile(p) (nearest rank; returns the bucket's highest equivalent value, min(max) capped)
    .nonzero() -> list[(index, count)]
    index_of(v, sub_bits) ; bucket_range(index, sub_bits) -> (lo, hi) inclusive
"""


def index_of(v, sub_bits=8):
    if v < (1 << sub_bits):
        return v
    shift = v.bit_length() - sub_bits
    mant = v >> shift
    half = 1 << (sub_bits - 1)
    return (1 << sub_bits) + (shift - 1) * half + (mant - half)


def bucket_range(i, sub_bits=8):
    full = 1 << sub_bits
    if i < full:
        return i, i
    half = full >> 1
    shift = (i - full) // half + 1
    mant = (i - full) % half + half
    return mant << shift, ((mant + 1) << shift) - 1


class LatHist:
    def __init__(self, sub_bits=8):
        self.sub_bits = sub_bits
        self.counts = [0] * (index_of((1 << 64) - 1, sub_bits) + 1)
        self.count = 0
        self.total = 0
        self.min = None
        self.max = 0

    def record(self, v, n=1):
        v = int(v)
        if v < 0:
            raise ValueError("latency must be non-negative")
        self.counts[index_of(v, self.sub_bits)] += n
        self.count += n
        self.total += v * n
        self.min = v if self.min is None else min(self.min, v)
        self.max = max(self.max, v)

    def record_corrected(self, v, interval):
        self.record(v)
        if interval <= 0:
            return
        missing = v - interval
        while missing > interval:
            self.record(missing)
            missing -= interval

    def merge(self, other):
        for i, c in enumerate(other.counts):
            self.counts[i] += c
        self.count += other.count
        self.total += other.total
        if other.min is not None:
            self.min = other.min if self.min is None else min(self.min, other.min)
        self.max = max(self.max, other.max)

    def mean(self):
        return self.total / self.count if self.count else 0.0

    def quantile(self, p):
        if not self.count:
            return 0
        rank = min(self.count, int(p * self.count) + 1)   # nearest rank, 1-based
        seen = 0
        for i, c in enumerate(self.counts):
            seen += c
            if seen >= rank:
                return min(bucket_range(i, self.sub_bits)[1], self.max)
        return self.max

    def nonzero(self):
        return [(i, c) for i, c in enumerate(self.counts) if c]
