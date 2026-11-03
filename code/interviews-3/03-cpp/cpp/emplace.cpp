#include <iostream>
#include <vector>

struct T {
    static inline int moves = 0;
    int x;
    T(int v) : x(v) {}
    T(T&& o) noexcept : x(o.x) { ++moves; }
};

int main() {
    std::vector<T> a;
    a.reserve(4);
    a.push_back(T(1));
    std::cout << T::moves << "\n";
    a.emplace_back(2);
    std::cout << T::moves << "\n";
    std::vector<std::vector<int>> rows;
    rows.emplace_back(1'000'000);
    std::cout << rows[0].size() << "\n";
    // try each line here
}
