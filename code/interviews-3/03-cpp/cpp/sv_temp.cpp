#include <iostream>
#include <string>
#include <string_view>

std::string make() { return std::string(40, 'x'); }

int main() {
    std::string_view v = make();
    std::cout << v.size() << " " << v[0] << "\n";
}
