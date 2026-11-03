#include <array>
#include <bit>
#include <cstddef>
#include <cstdint>
#include <cstdio>

class Histogram {
    static constexpr int kSubBits = 6;  // 64 buckets per doubling
    static constexpr int kMaxBits = 30;  // up to about 1.07 s in nanoseconds
    static constexpr std::size_t kSub = std::size_t{1} << kSubBits;

public:
    static constexpr std::size_t kBuckets = (kMaxBits - kSubBits + 1) * kSub;

    static std::size_t index(std::uint64_t v) {
        if (v >= (std::uint64_t{1} << kMaxBits)) return kBuckets - 1;  // saturate
        const int bits = std::bit_width(v);
        if (bits <= kSubBits) return static_cast<std::size_t>(v);
        const int shift = bits - kSubBits - 1;
        return (static_cast<std::size_t>(shift) + 1) * kSub
               + static_cast<std::size_t>((v >> shift) - kSub);
    }
    static std::uint64_t lower_bound(std::size_t i) {
        if (i < 2 * kSub) return i;
        const int shift = static_cast<int>(i / kSub) - 1;
        return static_cast<std::uint64_t>(kSub + i % kSub) << shift;
    }
    void record(std::uint64_t v) { ++counts_[index(v)]; }
    std::uint64_t percentile(double p) const {
        std::uint64_t total = 0, seen = 0;
        for (auto c : counts_) total += c;
        for (std::size_t i = 0; i < kBuckets; ++i) {
            seen += counts_[i];
            if (static_cast<double>(seen) >= p * static_cast<double>(total)) return lower_bound(i);
        }
        return lower_bound(kBuckets - 1);
    }

private:
    std::array<std::uint64_t, kBuckets> counts_{};
};

int main() {
    Histogram h;
    std::uint64_t worst_num = 0, worst_den = 1;
    for (std::uint64_t v = 1; v < (std::uint64_t{1} << 30); v += 1 + v / 512) {
        std::size_t i = Histogram::index(v);
        std::uint64_t lo = Histogram::lower_bound(i);
        if (lo > v || (i + 1 < Histogram::kBuckets && Histogram::lower_bound(i + 1) <= v)) return 1;
        if ((v - lo) * worst_den > worst_num * v) {
            worst_num = v - lo;
            worst_den = v;
        }
    }
    for (std::uint64_t v = 1; v <= 1000000; ++v) h.record(v);
    std::printf("%zu %zu\n", Histogram::kBuckets, sizeof(Histogram));
    std::printf("%llu %.5f\n", static_cast<unsigned long long>(h.percentile(0.99)),
                static_cast<double>(worst_num) / static_cast<double>(worst_den));
}
