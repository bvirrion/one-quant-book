#include "rc.hpp"
#include <cstdio>
#include <memory>
#include <random>
#include <thread>
#include <vector>

struct Val {
    static inline std::atomic<int> live{0};
    long x;
    long* heap;
    explicit Val(long v) : x(v), heap(new long(v)) { ++live; }
    Val(Val&& o) noexcept : x(o.x), heap(std::exchange(o.heap, nullptr)) { ++live; }
    ~Val() { delete heap; --live; }
};

int main() {
    std::mt19937 g(3);
    {   // one thread, against shared_ptr
        std::vector<Rc<Val>> m(6);
        std::vector<std::shared_ptr<long>> t(6);
        for (int i = 0; i < 20000; ++i) {
            int a = g() % 6, b = g() % 6;
            switch (g() % 4) {
                case 0: m[a] = Rc<Val>::make(long(i)); t[a] = std::make_shared<long>(i); break;
                case 1: m[a] = m[b]; t[a] = t[b]; break;
                case 2: m[a] = std::move(m[b]); t[a] = std::move(t[b]); break;
                case 3: m[a] = Rc<Val>{}; t[a].reset(); break;
            }
            for (int k = 0; k < 6; ++k) {
                if (m[k].count() != t[k].use_count()) { std::puts("count"); return 1; }
                if (m[k] && *m[k]->heap != *t[k]) { std::puts("value"); return 1; }
            }
        }
    }
    if (Val::live != 0) { std::puts("live"); return 1; }
    for (int round = 0; round < 300; ++round) {  // threads race to drop the last reference
        auto root = Rc<Val>::make(5L);
        std::vector<std::thread> ts;
        std::atomic<long> sum{0};
        for (int k = 0; k < 4; ++k)
            ts.emplace_back([p = root, &sum]() mutable {
                sum += *p->heap;
                Rc<Val> keep = p;
                p = Rc<Val>{};
                sum += keep->x;
            });
        root = Rc<Val>{};
        for (auto& t : ts) t.join();
        if (sum != 40) { std::puts("sum"); return 1; }
    }
    std::printf("%d\n", Val::live.load());
}
