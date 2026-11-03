#pragma once
#include <new>
#include <utility>

template <class T>
class Opt {
    alignas(T) unsigned char buf_[sizeof(T)];
    bool has_ = false;

    T* ptr() { return std::launder(reinterpret_cast<T*>(buf_)); }
    const T* ptr() const { return std::launder(reinterpret_cast<const T*>(buf_)); }

public:
    Opt() noexcept {}
    ~Opt() { reset(); }
    Opt(const Opt& o) { if (o.has_) emplace(*o.ptr()); }
    Opt(Opt&& o) noexcept(noexcept(T(std::declval<T&&>()))) {
        if (o.has_) emplace(std::move(*o.ptr()));
    }
    Opt& operator=(Opt o) {                      // copy made first, so self-assign is safe
        reset();
        if (o.has_) emplace(std::move(*o.ptr()));
        return *this;
    }
    template <class... A>
    T& emplace(A&&... a) {
        reset();
        T* p = ::new (static_cast<void*>(buf_)) T(std::forward<A>(a)...);
        has_ = true;                             // only after the constructor succeeds
        return *p;
    }
    void reset() noexcept {
        if (has_) ptr()->~T();
        has_ = false;
    }
    explicit operator bool() const noexcept { return has_; }
    T& operator*() { return *ptr(); }
    const T& operator*() const { return *ptr(); }
};
