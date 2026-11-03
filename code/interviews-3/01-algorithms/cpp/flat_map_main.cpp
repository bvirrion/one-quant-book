// Reads "p k v", "g k" or "e k" and prints each get's result, or "-" when absent.
#include "flat_map.hpp"

#include <iostream>

int main() {
    FlatMap m(1024);
    char op;
    std::uint64_t k, v;
    while (std::cin >> op >> k) {
        if (op == 'p') {
            std::cin >> v;
            m.put(k, v);
        } else if (op == 'e') {
            m.erase(k);
        } else if (auto r = m.get(k)) {
            std::cout << *r << '\n';
        } else {
            std::cout << "-\n";
        }
    }
}
