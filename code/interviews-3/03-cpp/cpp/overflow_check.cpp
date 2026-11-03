#include <climits>
#include <iostream>

[[gnu::noinline]] bool overflows(int a, int b) {     // for b > 0
    return a + b < a;
}

[[gnu::noinline]] bool safely(int a, int b) {
    int r;
    return __builtin_add_overflow(a, b, &r);
}

int main() {
    std::cout << overflows(INT_MAX, 1) << " " << safely(INT_MAX, 1) << "\n";
}
