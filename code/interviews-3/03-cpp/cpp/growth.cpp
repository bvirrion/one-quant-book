#include <iostream>
#include <vector>

struct Item {
    static inline long moves = 0;
    Item() = default;
    Item(const Item&) { ++moves; }
    Item(Item&&) noexcept { ++moves; }
};

int main() {
    std::vector<Item> v;
    std::size_t last = 0;
    for (int i = 0; i < 1000; ++i) {
        v.emplace_back();
        if (v.capacity() != last) {
            last = v.capacity();
            std::cout << last << " ";
        }
    }
    std::cout << "\n" << Item::moves << "\n";
}
