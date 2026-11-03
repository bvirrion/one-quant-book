#include <iostream>
#include <memory>
#include <string>
#include <utility>

int main() {
    std::string a(40, 'x');
    std::string b = std::move(a);
    std::cout << a.size() << " " << b.size() << "\n";
    a = "new";
    std::cout << a.size() << "\n";
    int i = 1;
    int j = std::move(i);
    std::cout << i << " " << j << "\n";
    auto p = std::make_unique<int>(5);
    auto q = std::move(p);
    std::cout << (p == nullptr) << " " << *q << "\n";
    std::string&& r = std::move(a);
    r += "!";
    std::cout << a << "\n";
}
