#include <iostream>
#include <vector>

int main() {
    std::vector<int> w{0, 0};
    auto y = w[0];
    y = 1;
    std::vector<bool> v{false, false};
    auto x = v[0];
    x = true;
    std::cout << w[0] << " " << y << " " << v[0] << "\n";
    // try each line here
}
