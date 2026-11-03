#include "pool.hpp"
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <random>

static long news = 0;
[[gnu::noinline]] void* operator new(std::size_t n) {
    ++news;
    if (void* p = std::malloc(n)) return p;
    throw std::bad_alloc{};
}
[[gnu::noinline]] void operator delete(void* p) noexcept { std::free(p); }
[[gnu::noinline]] void operator delete(void* p, std::size_t) noexcept { std::free(p); }

struct Boom {};
struct Order {
    static inline int live = 0, boom = 0;
    long id;
    explicit Order(long i) : id(i) { if (boom) throw Boom{}; ++live; }
    ~Order() { --live; }
};
struct alignas(64) Wide { char c = 'w'; };

int main() {
    static Pool<Order, 16> pool;
    Order* held[16];
    int n = 0;
    std::mt19937 g(11);
    long start = news;
    for (int i = 0; i < 100000; ++i) {
        if (g() % 2 && n > 0) {
            int k = g() % n;
            if (held[k]->id != reinterpret_cast<std::intptr_t>(held[k])) { std::puts("value"); return 1; }
            pool.destroy(held[k]);
            held[k] = held[--n];
        } else if (g() % 8 == 0 && n < 16) {
            Order::boom = 1;
            try { pool.create(0L); } catch (const Boom&) {}
            Order::boom = 0;
        } else {
            Order* p = pool.create(0L);
            if ((p == nullptr) != (n == 16)) { std::puts("exhaustion"); return 1; }
            if (p) { p->id = reinterpret_cast<std::intptr_t>(p); held[n++] = p; }
        }
        if (Order::live != n) { std::puts("live"); return 1; }
    }
    long used = news - start;
    while (n > 0) pool.destroy(held[--n]);
    Order* a = pool.create(1L);
    pool.destroy(a);
    Order* b = pool.create(2L);                  // the slot just freed comes back first
    std::printf("%ld %d\n", used, a == b);
    static Pool<Wide, 3> wide;
    Wide* w1 = wide.create();
    Wide* w2 = wide.create();
    std::printf("%d %d\n", int(reinterpret_cast<std::uintptr_t>(w1) % 64),
                int(reinterpret_cast<std::uintptr_t>(w2) % 64));
}
