#include "expr.hpp"
#include <iostream>

int main() {
    Vector a(4, 1.0), b(4, 2.0), c(4, 3.0);
    auto e = a + b + c;                 // the inner a + b dies at the end of this line
    std::cout << e[0] << "\n";
}
