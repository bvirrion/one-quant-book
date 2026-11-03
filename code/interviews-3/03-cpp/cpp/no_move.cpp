#include <iostream>
#include <utility>

struct Tracked {
    static inline int copies = 0, moves = 0;
    Tracked() = default;
    Tracked(const Tracked&) { ++copies; }
    Tracked(Tracked&&) noexcept { ++moves; }
};

struct Plain { Tracked t; };
struct Logged { Tracked t; ~Logged() {} };

template <class H>
void show() {
    Tracked::copies = Tracked::moves = 0;
    H a;
    H b = std::move(a);
    (void)b;
    std::cout << Tracked::copies << " " << Tracked::moves << "\n";
}

int main() {
    show<Plain>();
    show<Logged>();
}
