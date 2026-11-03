#include <iostream>
#include <numeric>
#include <vector>

int main() {
    std::vector<double> fills{0.6, 0.6, 0.6};
    std::cout << std::accumulate(fills.begin(), fills.end(), 0) << "\n";
    std::cout << std::accumulate(fills.begin(), fills.end(), 0.0) << "\n";
}
