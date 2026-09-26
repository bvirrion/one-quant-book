// firm.arena -- allocation-free building blocks for the hot path (build of One Quant Book 13, chapter 6).
// Header only, C++20.
//   Arena            bump allocator over one pre-faulted block; reset() frees everything at once
//   Pool<T, N>       fixed-capacity object pool with an intrusive free list: O(1) create/destroy, no heap
//   FixedVector<T,N> a vector whose storage is inside the object; push_back past N is refused
//   FixedString<N>   a short string stored inline (symbols, client order ids)
// The allocation counter used by the tests is in firm_alloc_count.hpp (it replaces global operator new, so it
// must be included by exactly one translation unit).
#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <memory>
#include <new>
#include <string_view>
#include <utility>
#include <vector>

namespace firm::arena {

class Arena {
public:
    explicit Arena(std::size_t bytes) : buf_(bytes) { std::memset(buf_.data(), 0, bytes); }  // pre-fault now
    void* allocate(std::size_t n, std::size_t align = alignof(std::max_align_t)) {
        const std::size_t at = (used_ + align - 1) & ~(align - 1);
        if (at + n > buf_.size()) return nullptr;  // full: the caller decides; never falls back to the heap
        used_ = at + n;
        return buf_.data() + at;
    }
    template <class T, class... A>
    T* make(A&&... a) {
        void* p = allocate(sizeof(T), alignof(T));
        return p ? new (p) T(std::forward<A>(a)...) : nullptr;
    }
    void reset() { used_ = 0; }  // objects must be trivially destructible or already destroyed
    std::size_t used() const { return used_; }
    std::size_t capacity() const { return buf_.size(); }

private:
    std::vector<std::byte> buf_;
    std::size_t used_ = 0;
};

template <class T, std::size_t N>
class Pool {
    union Slot {
        Slot* next;
        alignas(T) std::byte storage[sizeof(T)];
    };

public:
    Pool() : slots_(std::make_unique<Slot[]>(N)) {
        for (std::size_t i = 0; i + 1 < N; ++i) slots_[i].next = &slots_[i + 1];
        slots_[N - 1].next = nullptr;
        free_ = &slots_[0];
    }
    template <class... A>
    T* create(A&&... a) {
        if (!free_) return nullptr;  // exhausted: refuse, never allocate
        Slot* s = free_;
        free_ = s->next;
        ++live_;
        return new (s->storage) T(std::forward<A>(a)...);
    }
    void destroy(T* p) {
        p->~T();
        Slot* s = reinterpret_cast<Slot*>(p);
        s->next = free_;
        free_ = s;
        --live_;
    }
    std::size_t live() const { return live_; }
    static constexpr std::size_t capacity() { return N; }

private:
    std::unique_ptr<Slot[]> slots_;
    Slot* free_ = nullptr;
    std::size_t live_ = 0;
};

template <class T, std::size_t N>
class FixedVector {
public:
    bool push_back(const T& v) {
        if (n_ == N) return false;
        data_[n_++] = v;
        return true;
    }
    void clear() { n_ = 0; }
    std::size_t size() const { return n_; }
    T& operator[](std::size_t i) { return data_[i]; }
    const T& operator[](std::size_t i) const { return data_[i]; }
    T* begin() { return data_.data(); }
    T* end() { return data_.data() + n_; }

private:
    std::array<T, N> data_{};
    std::size_t n_ = 0;
};

template <std::size_t N>
class FixedString {
public:
    FixedString() = default;
    explicit FixedString(std::string_view s) { assign(s); }
    bool assign(std::string_view s) {
        if (s.size() > N) return false;
        std::memcpy(buf_.data(), s.data(), s.size());
        len_ = static_cast<std::uint8_t>(s.size());
        return true;
    }
    std::string_view view() const { return {buf_.data(), len_}; }
    bool operator==(const FixedString& o) const { return view() == o.view(); }

private:
    static_assert(N < 256);
    std::array<char, N> buf_{};
    std::uint8_t len_ = 0;
};

}  // namespace firm::arena
