// firm.lathist -- log-linear latency histogram (build of One Quant Book 13, chapter 5), C++20, header only.
// Same bucket layout as firm_lathist.py; reproduces data/fixture_buckets.csv and fixture_quantiles.csv.
// Recording is branch-light integer arithmetic on a fixed table: no allocation after construction.
#pragma once
#include <algorithm>
#include <bit>
#include <cstdint>
#include <vector>

namespace firm::lathist {

inline std::size_t index_of(std::uint64_t v, unsigned sub_bits = 8) {
    if (v < (std::uint64_t{1} << sub_bits)) return static_cast<std::size_t>(v);
    const unsigned shift = static_cast<unsigned>(std::bit_width(v)) - sub_bits;
    const std::uint64_t half = std::uint64_t{1} << (sub_bits - 1);
    const std::uint64_t mant = v >> shift;
    return static_cast<std::size_t>((std::uint64_t{1} << sub_bits) + (shift - 1) * half + (mant - half));
}

inline std::uint64_t bucket_high(std::size_t i, unsigned sub_bits = 8) {
    const std::uint64_t full = std::uint64_t{1} << sub_bits, half = full >> 1;
    if (i < full) return i;
    const std::uint64_t shift = (i - full) / half + 1, mant = (i - full) % half + half;
    return ((mant + 1) << shift) - 1;
}

class LatHist {
public:
    explicit LatHist(unsigned sub_bits = 8) : sub_bits_(sub_bits), counts_(index_of(~std::uint64_t{0}, sub_bits) + 1, 0) {}

    void record(std::uint64_t v, std::uint64_t n = 1) {
        counts_[index_of(v, sub_bits_)] += n;
        count_ += n;
        total_ += static_cast<double>(v) * static_cast<double>(n);
        min_ = std::min(min_, v);
        max_ = std::max(max_, v);
    }

    // Tene's correction for coordinated omission: add the samples a closed-loop tester failed to send.
    void record_corrected(std::uint64_t v, std::uint64_t interval) {
        record(v);
        if (interval == 0) return;
        for (std::uint64_t missing = v - std::min(v, interval); missing > interval; missing -= interval) record(missing);
    }

    void merge(const LatHist& o) {
        for (std::size_t i = 0; i < counts_.size(); ++i) counts_[i] += o.counts_[i];
        count_ += o.count_;
        total_ += o.total_;
        min_ = std::min(min_, o.min_);
        max_ = std::max(max_, o.max_);
    }

    std::uint64_t quantile(double p) const {
        if (count_ == 0) return 0;
        const auto rank = std::min(count_, static_cast<std::uint64_t>(p * static_cast<double>(count_)) + 1);
        std::uint64_t seen = 0;
        for (std::size_t i = 0; i < counts_.size(); ++i) {
            seen += counts_[i];
            if (seen >= rank) return std::min(bucket_high(i, sub_bits_), max_);
        }
        return max_;
    }

    std::uint64_t count() const { return count_; }
    std::uint64_t min() const { return count_ ? min_ : 0; }
    std::uint64_t max() const { return max_; }
    double mean() const { return count_ ? total_ / static_cast<double>(count_) : 0.0; }
    const std::vector<std::uint64_t>& counts() const { return counts_; }

private:
    unsigned sub_bits_;
    std::vector<std::uint64_t> counts_;
    std::uint64_t count_ = 0, min_ = ~std::uint64_t{0}, max_ = 0;
    double total_ = 0.0;
};

}  // namespace firm::lathist
