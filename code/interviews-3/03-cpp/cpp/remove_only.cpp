#include <algorithm>
#include <iostream>
#include <vector>

int main() {
    std::vector<int> v{1, 0, 2, 0, 3};
    auto end = std::remove(v.begin(), v.end(), 0);
    std::cout << v.size() << ":";
    for (int x : v) std::cout << " " << x;
    std::cout << "\n";
    v.erase(end, v.end());
    std::cout << v.size() << "\n";
}
