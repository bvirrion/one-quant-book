#pragma once
#include <utility>

template <class T>
class Unique {
    T* p_ = nullptr;

public:
    Unique() = default;
    explicit Unique(T* p) : p_(p) {}
    ~Unique() { delete p_; }
    Unique(const Unique&) = delete;
    Unique& operator=(const Unique&) = delete;
    Unique(Unique&& o) noexcept : p_(std::exchange(o.p_, nullptr)) {}
    Unique& operator=(Unique&& o) noexcept {
        reset(o.release());                  // safe on self-move
        return *this;
    }
    T* release() noexcept { return std::exchange(p_, nullptr); }
    void reset(T* p = nullptr) noexcept {
        T* old = std::exchange(p_, p);       // the object may hold a Unique to us
        delete old;
    }
    T* get() const noexcept { return p_; }
    T& operator*() const { return *p_; }
    T* operator->() const noexcept { return p_; }
    explicit operator bool() const noexcept { return p_ != nullptr; }
};
