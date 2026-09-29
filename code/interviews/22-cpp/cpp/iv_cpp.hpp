// Book 18, chapter 22: the C++20 coding answers.
#pragma once
#include <array>
#include <concepts>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <optional>
#include <utility>

namespace iv {

// A buffer that owns raw memory: the rule of five, with moves that leave the source empty.
class Buffer {
public:
    explicit Buffer(std::size_t n) : size_(n), data_(n ? new std::int64_t[n]() : nullptr) {}
    ~Buffer() { delete[] data_; }
    Buffer(const Buffer& o) : Buffer(o.size_) { std::copy(o.data_, o.data_ + size_, data_); }
    Buffer& operator=(const Buffer& o) {
        if (this != &o) {
            Buffer tmp(o);  // copy-and-swap: strong exception guarantee
            swap(tmp);
        }
        return *this;
    }
    Buffer(Buffer&& o) noexcept
        : size_(std::exchange(o.size_, 0)), data_(std::exchange(o.data_, nullptr)) {}
    Buffer& operator=(Buffer&& o) noexcept {
        if (this != &o) {
            delete[] data_;
            size_ = std::exchange(o.size_, 0);
            data_ = std::exchange(o.data_, nullptr);
        }
        return *this;
    }
    void swap(Buffer& o) noexcept {
        std::swap(size_, o.size_);
        std::swap(data_, o.data_);
    }
    std::size_t size() const { return size_; }
    std::int64_t& operator[](std::size_t i) { return data_[i]; }

private:
    std::size_t size_;
    std::int64_t* data_;
};

// Single-threaded fixed-capacity ring buffer; N is a power of two: indices wrap with a mask.
template <typename T, std::size_t N>
    requires(N > 0 && (N & (N - 1)) == 0)
class RingBuffer {
public:
    bool push(const T& v) {
        if (tail_ - head_ == N) return false;  // full: the caller decides (drop, block, grow)
        buf_[tail_++ & (N - 1)] = v;
        return true;
    }
    std::optional<T> pop() {
        if (head_ == tail_) return std::nullopt;
        return buf_[head_++ & (N - 1)];
    }
    std::size_t size() const { return tail_ - head_; }

private:
    std::array<T, N> buf_{};
    std::size_t head_ = 0, tail_ = 0;  // unsigned counters: wrap-around is well defined
};

// Compile-time table of powers of ten for integer price scaling.
constexpr std::array<std::int64_t, 19> pow10_table() {
    std::array<std::int64_t, 19> t{};
    t[0] = 1;
    for (std::size_t i = 1; i < t.size(); ++i) t[i] = t[i - 1] * 10;  // stops at 10^18
    return t;
}
inline constexpr auto kPow10 = pow10_table();

// A concept for anything that looks like an order: an integer price and quantity.
template <typename O>
concept OrderLike = requires(const O& o) {
    { o.price } -> std::convertible_to<std::int64_t>;
    { o.qty } -> std::convertible_to<std::int64_t>;
};

template <OrderLike O>
constexpr std::int64_t notional(const O& o) {
    return o.price * o.qty;
}

}  // namespace iv
