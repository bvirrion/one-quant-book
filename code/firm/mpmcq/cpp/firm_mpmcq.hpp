// firm.mpmcq -- bounded multi-producer multi-consumer queue (build of One Quant Book 13, chapter 11), C++20.
// The design of D. Vyukov's bounded MPMC queue: a power-of-two array of cells, each with a sequence number that says
// whose turn it is (a producer for position p when seq == p, a consumer when seq == p + 1); one compare-and-swap on
// the shared position per operation; no allocation after construction. Not lock-free in the strict sense: a producer
// stopped between claiming a cell and publishing it delays the consumers of that cell.
#pragma once
#include <atomic>
#include <cstddef>
#include <memory>
#include <new>
#include <optional>

#include "../../memkit/cpp/firm_memkit.hpp"

namespace firm::mpmcq {

template <class T>
class Queue {
    struct Cell {
        std::atomic<std::size_t> seq;
        T value;
    };

public:
    explicit Queue(std::size_t capacity) : mask_(capacity - 1), cells_(std::make_unique<Cell[]>(capacity)) {
        if (capacity < 2 || (capacity & (capacity - 1)) != 0) throw std::invalid_argument("capacity must be a power of two");
        for (std::size_t i = 0; i < capacity; ++i) cells_[i].seq.store(i, std::memory_order_relaxed);
    }

    bool try_push(const T& v) {
        std::size_t pos = tail_.value.load(std::memory_order_relaxed);
        for (;;) {
            Cell& c = cells_[pos & mask_];
            const std::size_t seq = c.seq.load(std::memory_order_acquire);
            const auto diff = static_cast<std::ptrdiff_t>(seq) - static_cast<std::ptrdiff_t>(pos);
            if (diff == 0) {  // the cell is free for position pos: claim the position
                if (tail_.value.compare_exchange_weak(pos, pos + 1, std::memory_order_relaxed)) {
                    c.value = v;
                    c.seq.store(pos + 1, std::memory_order_release);  // publish to the consumer of pos
                    return true;
                }
            } else if (diff < 0) {
                return false;  // full: the cell still holds the value from a lap ago
            } else {
                pos = tail_.value.load(std::memory_order_relaxed);  // another producer took pos
            }
        }
    }

    std::optional<T> try_pop() {
        std::size_t pos = head_.value.load(std::memory_order_relaxed);
        for (;;) {
            Cell& c = cells_[pos & mask_];
            const std::size_t seq = c.seq.load(std::memory_order_acquire);
            const auto diff = static_cast<std::ptrdiff_t>(seq) - static_cast<std::ptrdiff_t>(pos + 1);
            if (diff == 0) {
                if (head_.value.compare_exchange_weak(pos, pos + 1, std::memory_order_relaxed)) {
                    T v = c.value;
                    c.seq.store(pos + mask_ + 1, std::memory_order_release);  // free the cell for the next lap
                    return v;
                }
            } else if (diff < 0) {
                return std::nullopt;  // empty
            } else {
                pos = head_.value.load(std::memory_order_relaxed);
            }
        }
    }

    std::size_t capacity() const { return mask_ + 1; }

private:
    const std::size_t mask_;
    std::unique_ptr<Cell[]> cells_;
    memkit::CachePadded<std::atomic<std::size_t>> tail_{};  // producers and consumers on separate lines
    memkit::CachePadded<std::atomic<std::size_t>> head_{};
};

}  // namespace firm::mpmcq
