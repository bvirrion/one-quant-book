#pragma GCC diagnostic ignored "-Wsizeof-array-argument"
#include <iostream>
#include <iterator>

void show(int a[10]) { std::cout << sizeof(a) << "\n"; }

int main() {
    int a[10] = {};
    std::cout << sizeof(a) << "\n";
    show(a);
    std::cout << std::size(a) << "\n";
}
