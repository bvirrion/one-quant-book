// Acceptance test of firm.arena, C++ side: behaviour and zero heap allocations after construction.
#include "firm_arena.hpp"
#include "firm_alloc_count.hpp"

#include <cstdio>

using namespace firm::arena;

struct Order { std::uint64_t id; std::int64_t price; std::uint32_t qty; char side; };

int main() {
    Arena a(1 << 16);
    Pool<Order, 1024> pool;
    FixedVector<Order*, 16> live;
    const auto before = allocations();
    // arena: aligned bumps, refuse when full, reset
    auto* x = a.make<Order>(Order{1, 100, 5, 'B'});
    void* y = a.allocate(3, 1);
    auto* z = a.make<std::uint64_t>(7u);
    if (!x || !y || !z || reinterpret_cast<std::uintptr_t>(z) % alignof(std::uint64_t) != 0) return 1;
    if (a.allocate(1 << 17) != nullptr) return 1;
    a.reset();
    if (a.used() != 0) return 1;
    // pool: create, destroy out of order, reuse, exhaust
    for (int i = 0; i < 16; ++i) live.push_back(pool.create(Order{static_cast<std::uint64_t>(i), 100, 1, 'S'}));
    if (live.push_back(nullptr)) return 1;  // full
    pool.destroy(live[3]);
    pool.destroy(live[7]);
    Order* r = pool.create(Order{99, 1, 1, 'B'});
    if (r != live[7] || pool.live() != 15) return 1;  // last freed, first reused
    std::size_t made = 0;
    while (pool.create(Order{0, 0, 0, 'B'})) ++made;
    if (made != 1024 - 15) return 1;
    FixedString<14> s("ORD-000123");
    if (s.view() != "ORD-000123" || s.assign("123456789012345")) return 1;
    if (allocations() != before) { std::printf("%llu heap allocations on the hot path\n", allocations() - before); return 1; }
    std::puts("arena ok");
    return 0;
}
