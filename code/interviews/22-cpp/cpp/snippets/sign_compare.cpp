#include <cstdio>

int main() {
    int balance = -1;
    unsigned limit = 1;
    if (balance < limit) std::printf("within limit\n");
    else std::printf("over limit\n");
    std::printf("%u\n", static_cast<unsigned>(balance));
}
