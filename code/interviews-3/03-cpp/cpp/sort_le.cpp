#include <algorithm>
#include <iostream>
#include <vector>

int main() {
    std::vector<int> v(100, 1);
    std::sort(v.begin(), v.end(), [](int a, int b) { return a <= b; });
    std::cout << v.size() << "\n";
}
