#include <iostream>
#include <stdexcept>
#include <string>
#include <variant>

struct Fragile {
    std::string s;
    explicit Fragile(int) { throw std::runtime_error("no"); }
};

int main() {
    std::variant<int, Fragile> v = 5;
    try {
        v.emplace<Fragile>(1);
    } catch (const std::runtime_error&) {
    }
    std::cout << v.valueless_by_exception() << " " << (v.index() == std::variant_npos) << "\n";
}
