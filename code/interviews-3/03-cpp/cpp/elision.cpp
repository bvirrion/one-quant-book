#pragma GCC diagnostic ignored "-Wpessimizing-move"
#include <iostream>
#include <utility>

struct T {
    static inline int copies = 0, moves = 0;
    T() = default;
    T(const T&) { ++copies; }
    T(T&&) noexcept { ++moves; }
};

T plain() { T t; return t; }
T forced() { T t; return std::move(t); }
T either(bool c) { T p, q; return c ? p : q; }

struct Pinned {
    Pinned() = default;
    Pinned(const Pinned&) = delete;
};
Pinned make() { return Pinned{}; }

template <class F>
void show(const char* name, F f) {
    T::copies = T::moves = 0;
    { auto r = f(); (void)r; }
    std::cout << name << ": " << T::copies << " copies, " << T::moves << " moves\n";
}

int main() {
    show("plain", [] { return plain(); });
    show("forced", [] { return forced(); });
    show("either", [] { return either(true); });
    Pinned p = make();
    (void)p;
}
