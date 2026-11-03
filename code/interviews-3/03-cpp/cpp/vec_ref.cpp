#include <iostream>
#include <vector>

int main() {
    std::vector<int> v{1, 2, 3};
    int& first = v[0];
    v.push_back(4);
    first = 9;
    std::cout << v[0] << "\n";
}
