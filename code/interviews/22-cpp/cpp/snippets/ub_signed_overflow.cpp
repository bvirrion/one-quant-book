#include <climits>
#include <cstdio>

int main(int argc, char**) {
    int qty = INT_MAX - 1 + argc;  // INT_MAX when run without arguments
    int doubled = qty * 2;         // signed overflow
    std::printf("%d\n", doubled);
}
