// Acceptance test of firm.mpmcq: FIFO, full and empty, then a stress test (2 producers, 2 consumers, a few hundred
// thousand items, bounded to a few seconds) checking that every item is delivered exactly once.
#include "firm_mpmcq.hpp"

#include <cstdio>
#include <thread>
#include <vector>

using firm::mpmcq::Queue;

int main() {
    Queue<int> q(4);
    for (int i = 0; i < 4; ++i) if (!q.try_push(i)) return 1;
    if (q.try_push(9)) return 1;  // full
    for (int i = 0; i < 4; ++i) if (q.try_pop() != i) return 1;
    if (q.try_pop()) return 1;  // empty

    constexpr int producers = 2, consumers = 2, per = 150'000;
    Queue<std::uint32_t> s(1024);
    std::vector<std::atomic<std::uint8_t>> seen(static_cast<std::size_t>(producers * per));
    std::atomic<int> done{0};
    std::vector<std::thread> ts;
    for (int p = 0; p < producers; ++p)
        ts.emplace_back([&, p] {
            for (int i = 0; i < per; ++i)
                while (!s.try_push(static_cast<std::uint32_t>(p * per + i))) std::this_thread::yield();
        });
    for (int c = 0; c < consumers; ++c)
        ts.emplace_back([&] {
            while (done.load() < producers * per) {
                if (auto v = s.try_pop()) { seen[*v].fetch_add(1); done.fetch_add(1); }
                else std::this_thread::yield();
            }
        });
    for (auto& t : ts) t.join();
    for (auto& x : seen) if (x.load() != 1) { std::puts("an item was lost or duplicated"); return 1; }
    std::puts("mpmcq ok");
    return 0;
}
