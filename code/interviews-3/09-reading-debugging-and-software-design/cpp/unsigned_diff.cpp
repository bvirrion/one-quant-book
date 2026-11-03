#include <cstdio>
#include <vector>

int main() {
    std::vector<int> bids{10, 20};
    std::vector<int> asks{10, 20, 30};
    if (bids.size() - asks.size() > 0) {
        std::puts("more bids than asks");
    } else {
        std::puts("no more bids than asks");
    }
    std::printf("%zu\n", bids.size() - asks.size());
}
