#pragma once
#include <cstdint>
#include <optional>
#include <vector>

// Linear probing with backward-shift deletion. The key 0 marks an empty slot.
class FlatMap {
    std::vector<std::uint64_t> keys_, vals_;
    std::size_t mask_;

    std::size_t home(std::uint64_t k) const {
        return (k * 0x9E3779B97F4A7C15ULL >> 20) & mask_;
    }

public:
    explicit FlatMap(std::size_t power_of_two)
        : keys_(power_of_two), vals_(power_of_two), mask_(power_of_two - 1) {}

    void put(std::uint64_t k, std::uint64_t v) {       // k != 0, and the table never fills
        std::size_t i = home(k);
        while (keys_[i] != 0 && keys_[i] != k) i = (i + 1) & mask_;
        keys_[i] = k;
        vals_[i] = v;
    }
    std::optional<std::uint64_t> get(std::uint64_t k) const {
        for (std::size_t i = home(k); keys_[i] != 0; i = (i + 1) & mask_)
            if (keys_[i] == k) return vals_[i];
        return std::nullopt;
    }
    void erase(std::uint64_t k) {
        std::size_t i = home(k);
        while (keys_[i] != k) {
            if (keys_[i] == 0) return;
            i = (i + 1) & mask_;
        }
        for (std::size_t j = (i + 1) & mask_; keys_[j] != 0; j = (j + 1) & mask_) {
            if (((j - home(keys_[j])) & mask_) >= ((j - i) & mask_)) {  // j may move to i
                keys_[i] = keys_[j];
                vals_[i] = vals_[j];
                i = j;
            }
        }
        keys_[i] = 0;
    }
};
