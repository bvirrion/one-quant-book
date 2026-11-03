#include <iostream>
#include <vector>

template <bool NoThrow>
struct Item {
    static inline int copies = 0, moves = 0;
    Item() = default;
    Item(const Item&) { ++copies; }
    Item(Item&&) noexcept(NoThrow) { ++moves; }
};

template <class T>
void grow() {
    std::vector<T> v;
    for (int i = 0; i < 5; ++i) v.emplace_back();
    std::cout << T::copies << " copies, " << T::moves << " moves\n";
}

int main() {
    grow<Item<true>>();
    grow<Item<false>>();
}
