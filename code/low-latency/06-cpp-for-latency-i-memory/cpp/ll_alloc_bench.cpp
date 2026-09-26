// Chapter 6 benchmark. Modes:
//   churn  -> allocator,p50,p99,p999,max   ns per create+destroy pair, 10,000 live 64-byte orders replaced at random
//   faults -> kind,ns_per_page,faults       first write to each page of 64 MiB: fresh mapping against pre-faulted
#include <sys/mman.h>
#include <sys/resource.h>

#include <cstdio>
#include <cstring>
#include <memory>
#include <memory_resource>
#include <random>
#include <string>
#include <vector>

#include "firm_arena.hpp"
#include "firm_ubench.hpp"

using namespace firm::ubench;

struct Order { std::uint64_t id; std::int64_t price; std::uint32_t qty; char pad[44]; };
static_assert(sizeof(Order) == 64);

template <class Make, class Kill>
static void churn(const char* name, Make make, Kill kill, const Clock& clk) {
    constexpr std::size_t live_n = 10'000, ops = 400'000;
    std::vector<Order*> live(live_n);
    for (auto& p : live) p = make();
    std::mt19937_64 rng(3);
    std::vector<double> t;
    t.reserve(ops);
    for (std::size_t i = 0; i < ops; ++i) {
        const std::size_t k = rng() % live_n;
        const std::uint64_t a = tsc_start();
        kill(live[k]);
        live[k] = make();
        const std::uint64_t b = rdtscp();
        t.push_back(clk.ns(b - a));
    }
    for (auto p : live) kill(p);
    std::printf("%s,%.1f,%.1f,%.1f,%.1f\n", name, quantile(t, 0.5), quantile(t, 0.99), quantile(t, 0.999), quantile(t, 1.0));
}

static long minflt() { rusage r{}; getrusage(RUSAGE_SELF, &r); return r.ru_minflt; }

int main(int argc, char** argv) {
    const Clock clk = Clock::calibrate(50);
    if (argc < 2 || std::string(argv[1]) == "churn") {
        std::printf("allocator,p50,p99,p999,max\n");
        churn("new/delete", [] { return new Order{}; }, [](Order* p) { delete p; }, clk);
        auto pool = std::make_unique<firm::arena::Pool<Order, 10'000>>();
        churn("pool", [&] { return pool->create(); }, [&](Order* p) { pool->destroy(p); }, clk);
        std::pmr::unsynchronized_pool_resource res;
        churn("pmr pool", [&] { return new (res.allocate(sizeof(Order), alignof(Order))) Order{}; },
              [&](Order* p) { res.deallocate(p, sizeof(Order), alignof(Order)); }, clk);
    } else {
        constexpr std::size_t bytes = 64u << 20, page = 4096;
        std::printf("kind,ns_per_page,faults\n");
        for (int prefault = 0; prefault < 2; ++prefault) {
            auto* p = static_cast<char*>(mmap(nullptr, bytes, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0));
            madvise(p, bytes, MADV_NOHUGEPAGE);
            if (prefault) std::memset(p, 1, bytes);
            const long f0 = minflt();
            const std::uint64_t a = tsc_start();
            for (std::size_t i = 0; i < bytes; i += page) p[i] = 2;
            const std::uint64_t b = rdtscp();
            std::printf("%s,%.1f,%ld\n", prefault ? "pre-faulted" : "first touch", clk.ns(b - a) / (bytes / page), minflt() - f0);
            munmap(p, bytes);
        }
    }
    return 0;
}
