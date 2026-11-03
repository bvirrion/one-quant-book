#include <cstdio>
#include <vector>

int main() {
    std::vector<long> qty{10, 0, 0, 20};
    for (auto it = qty.begin(); it != qty.end(); ++it) {
        if (*it == 0) {
            qty.erase(it);
        }
    }
    for (long q : qty) std::printf("%ld ", q);
    std::puts("");
}
