#include "fn.hpp"
#include <array>
#include <cstdio>
#include <cstdlib>
#include <functional>
#include <memory>
#include <random>
#include <vector>

static long news = 0;
[[gnu::noinline]] void* operator new(std::size_t n) {
    ++news;
    if (void* p = std::malloc(n)) return p;
    throw std::bad_alloc{};
}
[[gnu::noinline]] void operator delete(void* p) noexcept { std::free(p); }
[[gnu::noinline]] void operator delete(void* p, std::size_t) noexcept { std::free(p); }

struct Live {
    static inline int n = 0;
    Live() { ++n; }
    Live(const Live&) { ++n; }
    Live(Live&&) noexcept { ++n; }
    ~Live() { --n; }
};

int main() {
    long start = news;
    long a = 1, b = 2, c = 3, d = 4;
    Fn<long(long)> small = [a, b, c, d](long x) { return a + b + c + d + x; };
    long smalls = news - start;
    start = news;
    std::array<long, 8> eight{1, 2, 3, 4, 5, 6, 7, 8};
    Fn<long(long)> big = [eight](long x) { return eight[7] + x; };
    long bigs = news - start;
    std::printf("%ld %ld %ld %ld\n", smalls, bigs, small(10), big(10));
    Fn<long(long)> moved = std::move(big);
    std::printf("%d %ld\n", bool(big), moved(1));
    auto up = std::make_unique<int>(7);                     // move-only capture
    Fn<int()> own = [u = std::move(up)] { return *u; };
    std::printf("%d\n", own());
    std::mt19937 g(1);
    {
        std::vector<Fn<long(long)>> mine(5);
        std::vector<std::function<long(long)>> theirs(5);
        for (int i = 0; i < 20000; ++i) {
            int k = g() % 5, j = g() % 5;
            long v = g() % 100;
            switch (g() % 4) {
                case 0: mine[k] = [v, l = Live{}](long x) { return x + v; };
                        theirs[k] = [v, l = Live{}](long x) { return x + v; }; break;
                case 1: { std::array<long, 8> w{v}; mine[k] = [w, l = Live{}](long x) { return x * w[0]; };
                          theirs[k] = [w, l = Live{}](long x) { return x * w[0]; }; break; }
                case 2: if (k != j) { mine[k] = std::move(mine[j]); theirs[k] = std::move(theirs[j]); theirs[j] = nullptr; } break;
                case 3: mine[k].reset(); theirs[k] = nullptr; break;
            }
            for (int q = 0; q < 5; ++q) {
                if (bool(mine[q]) != bool(theirs[q])) { std::puts("has"); return 1; }
                if (mine[q] && mine[q](i) != theirs[q](i)) { std::puts("value"); return 1; }
            }
        }
    }
    std::printf("%d\n", Live::n);
}
