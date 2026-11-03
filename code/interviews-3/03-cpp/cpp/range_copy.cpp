#include <iostream>
#include <vector>

int main() {
    std::vector<int> v{1, 2};
    for (auto x : v) x *= 10;
    std::cout << v[0] << " " << v[1] << "\n";
    for (auto& x : v) x *= 10;
    std::cout << v[0] << " " << v[1] << "\n";
    const int& r = v[0];
    auto a = r;
    a = 7;
    std::cout << v[0] << " " << a << "\n";
}
