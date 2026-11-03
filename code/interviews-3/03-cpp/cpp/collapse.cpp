#include <iostream>
#include <type_traits>
#include <vector>

template <class T>
const char* f(T&&) {
    return std::is_lvalue_reference_v<T> ? "T is a reference" : "T is a value";
}

template <class T>
void g(std::vector<T>&&) {}

int main() {
    int i = 1;
    const int k = 2;
    std::cout << f(i) << "\n" << f(1) << "\n" << f(k) << "\n";
    g(std::vector<int>{});
    auto&& a = i;
    auto&& b = 1;
    static_assert(std::is_same_v<decltype(a), int&>);
    static_assert(std::is_same_v<decltype(b), int&&>);
    // try each line here
}
