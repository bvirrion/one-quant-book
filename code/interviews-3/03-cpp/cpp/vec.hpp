#pragma once
#include <cstddef>
#include <memory>
#include <new>
#include <type_traits>
#include <utility>

template <class T>
class Vec {
    T* d_ = nullptr;
    std::size_t n_ = 0, cap_ = 0;
    static T* get(std::size_t c) { return std::allocator<T>{}.allocate(c); }
    void put() noexcept {
        std::destroy_n(d_, n_);
        if (d_) std::allocator<T>{}.deallocate(d_, cap_);
    }
    void transfer(T* to) {
        if constexpr (std::is_nothrow_move_constructible_v<T>
                      || !std::is_copy_constructible_v<T>)
            std::uninitialized_move_n(d_, n_, to);
        else
            std::uninitialized_copy_n(d_, n_, to);
    }

public:
    Vec() = default;
    ~Vec() { put(); }
    Vec(const Vec& o) : d_(get(o.n_)), cap_(o.n_) {
        try { std::uninitialized_copy_n(o.d_, o.n_, d_); }
        catch (...) { std::allocator<T>{}.deallocate(d_, cap_); throw; }
        n_ = o.n_;
    }
    Vec(Vec&& o) noexcept
        : d_(std::exchange(o.d_, nullptr)), n_(std::exchange(o.n_, 0)),
          cap_(std::exchange(o.cap_, 0)) {}
    Vec& operator=(Vec o) noexcept {
        std::swap(d_, o.d_); std::swap(n_, o.n_); std::swap(cap_, o.cap_);
        return *this;
    }
    template <class... A>
    T& emplace_back(A&&... a) {
        if (n_ < cap_) {
            T* p = ::new (static_cast<void*>(d_ + n_)) T(std::forward<A>(a)...);
            ++n_;
            return *p;
        }
        std::size_t c = cap_ ? 2 * cap_ : 1;
        T* fresh = get(c);
        T* slot = fresh + n_;
        try {
            ::new (static_cast<void*>(slot)) T(std::forward<A>(a)...);   // before the old go
            try { transfer(fresh); }
            catch (...) { slot->~T(); throw; }
        } catch (...) {
            std::allocator<T>{}.deallocate(fresh, c);
            throw;
        }
        put();
        d_ = fresh;
        cap_ = c;
        ++n_;
        return *slot;
    }
    void pop_back() noexcept { d_[--n_].~T(); }
    T& operator[](std::size_t i) { return d_[i]; }
    const T& operator[](std::size_t i) const { return d_[i]; }
    std::size_t size() const noexcept { return n_; }
    std::size_t capacity() const noexcept { return cap_; }
};
