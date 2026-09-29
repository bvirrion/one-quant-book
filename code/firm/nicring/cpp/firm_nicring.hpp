// firm.nicring (C++20): a network card's receive descriptor ring (One Quant Book 14, chapter 3). Same rules and same
// order of operations as the Python reference firm_nicring.py: the card fills descriptors it owns and hands them to the
// host; the host processes up to `budget` per poll and hands them back in batches of `refill` (one doorbell each).
#pragma once
#include <cstdint>
#include <stdexcept>
#include <vector>

namespace firm::nicring {

class Ring {
public:
    Ring(std::uint32_t size, std::uint32_t refill) : size_(size), refill_(refill), owner_(size, 0), seq_(size, 0),
                                                     len_(size, 0) {
        if ((size & (size - 1)) != 0 || refill < 1 || refill > size) throw std::invalid_argument("ring size or refill");
    }

    bool nic_rx(std::uint64_t seq, std::uint32_t length) {
        const std::uint32_t i = head_;
        if (owner_[i] == 1) { ++drops; return false; }   // still the host's: the ring is full
        seq_[i] = seq, len_[i] = length, owner_[i] = 1;
        head_ = (i + 1) & (size_ - 1);
        ++rx;
        return true;
    }

    std::uint32_t poll(std::uint32_t budget) {
        std::uint32_t n = 0;
        while (n < budget && rx > processed) {
            const std::uint32_t i = tail_;
            mix(seq_[i]), mix(len_[i]);
            tail_ = (i + 1) & (size_ - 1);
            ++processed, ++pending_, ++n;
            if (pending_ >= refill_) give_back();
        }
        return n;
    }

    void note_owned() {
        const std::uint64_t held = rx - processed + pending_;
        if (held > max_owned) max_owned = held;
    }

    std::uint64_t rx = 0, drops = 0, processed = 0, doorbells = 0, max_owned = 0;
    std::uint64_t hash = 0xCBF29CE484222325ULL;

private:
    void mix(std::uint64_t x) {
        for (int k = 0; k < 8; ++k, x >>= 8) hash = (hash ^ (x & 0xFF)) * 0x100000001B3ULL;
    }
    void give_back() {
        const std::uint32_t start = (tail_ - pending_) & (size_ - 1);
        for (std::uint32_t k = 0; k < pending_; ++k) owner_[(start + k) & (size_ - 1)] = 0;
        pending_ = 0;
        ++doorbells;
    }
    std::uint32_t size_, refill_, head_ = 0, tail_ = 0, pending_ = 0;
    std::vector<std::uint8_t> owner_;
    std::vector<std::uint64_t> seq_;
    std::vector<std::uint32_t> len_;
};

}  // namespace firm::nicring
