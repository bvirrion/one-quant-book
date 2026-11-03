#include <cstdint>
#include <iostream>

int main() {
    std::uint8_t a = 200, b = 100, e = 65;
    auto c = a + b;
    std::uint8_t d = a + b;
    std::cout << c << " " << sizeof(c) << "\n";
    std::cout << int(d) << "\n";
    std::cout << e << " " << int(e) << " " << +e << "\n";
}
