#include "expr.hpp"
#include <cstdio>
#include <cstdlib>
#include <new>
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

using Plain = std::vector<double>;
Plain operator+(const Plain& a, const Plain& b) {
    Plain out(a.size());
    for (std::size_t i = 0; i < a.size(); ++i) out[i] = a[i] + b[i];
    return out;
}

int main() {
    std::mt19937 g(4);
    const std::size_t n = 1000;
    Vector a(n), b(n), c(n), d(n);
    Plain pa(n), pb(n), pc(n), pd(n);
    for (std::size_t i = 0; i < n; ++i) {
        a[i] = pa[i] = g() % 100;
        b[i] = pb[i] = g() % 100;
        c[i] = pc[i] = g() % 100;
    }
    long before = news;
    d = a + b + c;
    long lazy = news - before;
    before = news;
    pd = pa + pb + pc;
    long eager = news - before;
    for (std::size_t i = 0; i < n; ++i)
        if (d[i] != pd[i]) { std::puts("value"); return 1; }
    a = a + b;                                    // same element on both sides: fine
    pa = pa + pb;
    for (std::size_t i = 0; i < n; ++i)
        if (a[i] != pa[i]) { std::puts("alias"); return 1; }
    std::printf("%ld %ld\n", lazy, eager);
}
