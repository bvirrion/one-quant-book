#pragma once
#include <atomic>
#include <utility>

template <class T>
class Rc {
    struct Block {
        std::atomic<long> refs{1};
        T value;
    };
    Block* b_ = nullptr;
    explicit Rc(Block* b) : b_(b) {}

public:
    template <class... A>
    static Rc make(A&&... a) { return Rc(new Block{{1}, T(std::forward<A>(a)...)}); }
    Rc() = default;
    ~Rc() {
        if (b_ && b_->refs.fetch_sub(1, std::memory_order_acq_rel) == 1) delete b_;
    }
    Rc(const Rc& o) noexcept : b_(o.b_) {
        if (b_) b_->refs.fetch_add(1, std::memory_order_relaxed);
    }
    Rc(Rc&& o) noexcept : b_(std::exchange(o.b_, nullptr)) {}
    Rc& operator=(Rc o) noexcept {               // copy or move first, then swap and drop
        std::swap(b_, o.b_);
        return *this;
    }
    T& operator*() const { return b_->value; }
    T* operator->() const { return &b_->value; }
    long count() const { return b_ ? b_->refs.load(std::memory_order_relaxed) : 0; }
    explicit operator bool() const { return b_ != nullptr; }
};
