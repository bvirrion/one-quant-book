#pragma once
#include <algorithm>
#include <cstddef>
#include <new>
#include <type_traits>
#include <utility>

template <class... Ts>
class Var {
    static constexpr std::size_t none = sizeof...(Ts);
    alignas(Ts...) unsigned char buf_[std::max({sizeof(Ts)...})];
    std::size_t idx_ = none;

    template <class T> static constexpr std::size_t index_of = [] {
        static_assert((std::is_same_v<T, Ts> || ...), "T is not in the list");
        std::size_t i = 0, found = none;
        ((std::is_same_v<T, Ts> ? void(found = i) : void(), ++i), ...);
        return found;
    }();
    template <class T> T* as() { return std::launder(reinterpret_cast<T*>(buf_)); }
    void destroy() noexcept {
        std::size_t i = 0;
        ((idx_ == i++ ? as<Ts>()->~Ts() : void()), ...);
        idx_ = none;
    }
public:
    Var() = default;
    Var(const Var&) = delete;
    Var& operator=(const Var&) = delete;
    ~Var() { destroy(); }
    template <class T, class... A> T& emplace(A&&... a) {
        destroy();                               // if the constructor throws: valueless
        T* p = ::new (static_cast<void*>(buf_)) T(std::forward<A>(a)...);
        idx_ = index_of<T>;
        return *p;
    }
    bool valueless() const noexcept { return idx_ == none; }
    std::size_t index() const noexcept { return idx_; }
    template <class T>
    T* get_if() noexcept { return idx_ == index_of<T> ? as<T>() : nullptr; }
    template <class F> auto visit(F&& f) {
        std::common_type_t<decltype(f(std::declval<Ts&>()))...> out{};
        std::size_t i = 0;
        ((idx_ == i++ ? void(out = f(*as<Ts>())) : void()), ...);
        return out;
    }
};
