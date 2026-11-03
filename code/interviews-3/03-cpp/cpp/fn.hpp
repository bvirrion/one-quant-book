#pragma once
#include <cstddef>
#include <new>
#include <type_traits>
#include <utility>

template <class Sig> class Fn;

template <class R, class... A>
class Fn<R(A...)> {
    static constexpr std::size_t Cap = 32;
    struct Ops {
        R (*call)(void*, A&&...);
        void (*move_to)(void* from, void* to) noexcept;   // constructs at to, destroys from
        void (*destroy)(void*) noexcept;
    };
    alignas(std::max_align_t) unsigned char buf_[Cap];
    const Ops* ops_ = nullptr;

    template <class F, bool Small> struct Model {
        static F* get(void* p) {
            if constexpr (Small) return std::launder(static_cast<F*>(p));
            else return *static_cast<F**>(p);
        }
        static inline const Ops ops{
            [](void* p, A&&... a) -> R { return (*get(p))(std::forward<A>(a)...); },
            [](void* from, void* to) noexcept {
                if constexpr (Small) { ::new (to) F(std::move(*get(from))); get(from)->~F(); }
                else ::new (to) F*(get(from));
            },
            [](void* p) noexcept {
                if constexpr (Small) get(p)->~F();
                else delete get(p);
            }};
    };

public:
    Fn() = default;
    template <class F, class D = std::decay_t<F>,
              class = std::enable_if_t<!std::is_same_v<D, Fn>>>
    Fn(F&& f) {
        constexpr bool small = sizeof(D) <= Cap && alignof(D) <= alignof(std::max_align_t)
                               && std::is_nothrow_move_constructible_v<D>;
        if constexpr (small) ::new (static_cast<void*>(buf_)) D(std::forward<F>(f));
        else ::new (static_cast<void*>(buf_)) D*(new D(std::forward<F>(f)));
        ops_ = &Model<D, small>::ops;
    }
    Fn(Fn&& o) noexcept : ops_(std::exchange(o.ops_, nullptr)) {
        if (ops_) ops_->move_to(o.buf_, buf_);
    }
    Fn& operator=(Fn o) noexcept {
        reset();
        if (o.ops_) { o.ops_->move_to(o.buf_, buf_); ops_ = std::exchange(o.ops_, nullptr); }
        return *this;
    }
    ~Fn() { reset(); }
    void reset() noexcept {
        if (ops_) ops_->destroy(buf_);
        ops_ = nullptr;
    }
    explicit operator bool() const noexcept { return ops_ != nullptr; }
    R operator()(A... a) { return ops_->call(buf_, std::forward<A>(a)...); }
};
