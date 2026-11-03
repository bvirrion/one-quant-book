#include <cstdio>
#include <cstdlib>

[[gnu::noinline]] long down(long n) {
    volatile char page[1024];
    page[0] = 1;
    return n == 0 ? 0 : down(n - 1) + page[0];
}

int main(int, char** argv) {
    std::printf("%ld\n", down(std::atol(argv[1])));
}
