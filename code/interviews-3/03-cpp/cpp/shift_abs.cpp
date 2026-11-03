#include <climits>
#include <cstdlib>
#include <iostream>

int main(int argc, char**) {
    int s = argc + 32;                       // 33 with no arguments
    int low = INT_MIN + argc - 1;            // INT_MIN with no arguments
    std::cout << (1 << 31) << "\n";
    std::cout << (1 << s) << "\n";
    std::cout << std::abs(low) << "\n";
    unsigned u = 0;
    std::cout << u - 1 << "\n";
}
