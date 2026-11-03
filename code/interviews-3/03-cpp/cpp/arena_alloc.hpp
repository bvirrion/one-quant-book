#pragma once
#include <cstddef>
#include <memory>
#include <new>

class Arena {
    void* cur_;
    std::size_t left_;

public:
    Arena(void* buf, std::size_t n) : cur_(buf), left_(n) {}
    void* take(std::size_t n, std::size_t align) {
        if (!std::align(align, n, cur_, left_)) throw std::bad_alloc{};
        void* p = cur_;
        cur_ = static_cast<char*>(cur_) + n;
        left_ -= n;
        return p;
    }
    std::size_t left() const { return left_; }
};

template <class T>
struct ArenaAlloc {
    using value_type = T;
    Arena* arena;
    explicit ArenaAlloc(Arena& a) noexcept : arena(&a) {}
    template <class U>
    ArenaAlloc(const ArenaAlloc<U>& o) noexcept : arena(o.arena) {}
    T* allocate(std::size_t n) {
        return static_cast<T*>(arena->take(n * sizeof(T), alignof(T)));
    }
    void deallocate(T*, std::size_t) noexcept {}
    template <class U>
    bool operator==(const ArenaAlloc<U>& o) const noexcept { return arena == o.arena; }
};
