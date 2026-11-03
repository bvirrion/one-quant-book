#include "arena_alloc.hpp"
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <map>
#include <vector>

static long news = 0;
[[gnu::noinline]] void* operator new(std::size_t n) {
    ++news;
    if (void* p = std::malloc(n)) return p;
    throw std::bad_alloc{};
}
[[gnu::noinline]] void operator delete(void* p) noexcept { std::free(p); }
[[gnu::noinline]] void operator delete(void* p, std::size_t) noexcept { std::free(p); }

int main() {
    alignas(64) static char buf[1 << 16];
    Arena arena(buf, sizeof buf);
    long start = news;
    std::vector<int, ArenaAlloc<int>> v{ArenaAlloc<int>(arena)};
    for (int i = 0; i < 100; ++i) v.push_back(i);
    using A = ArenaAlloc<std::pair<const int, double>>;
    std::map<int, double, std::less<int>, A> m{A(arena)};
    for (int i = 0; i < 100; ++i) m[i] = i * 0.5;
    long sum = 0;
    for (int x : v) sum += x;
    double total = 0;
    for (auto& [k, x] : m) total += x;
    arena.take(1, 1);
    double* d = static_cast<double*>(arena.take(8, alignof(double)));
    std::printf("%ld %ld %.1f %d\n", news - start, sum, total,
                int(reinterpret_cast<std::uintptr_t>(d) % alignof(double)));
    bool thrown = false;
    try {
        std::vector<int, ArenaAlloc<int>> big{ArenaAlloc<int>(arena)};
        big.reserve(1 << 20);
    } catch (const std::bad_alloc&) {
        thrown = true;
    }
    std::printf("%d\n", thrown);
}
