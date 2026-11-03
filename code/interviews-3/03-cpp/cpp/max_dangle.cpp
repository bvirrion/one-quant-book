#include <algorithm>
#include <iostream>

int main(int argc, char**) {
    const int& m = std::max(argc, 2);
    std::cout << m << "\n";
}
