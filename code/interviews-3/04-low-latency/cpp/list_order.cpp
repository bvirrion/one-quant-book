#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <list>
#include <numeric>
#include <random>
#include <vector>

std::int64_t sum(const std::list<std::int64_t>& l) {
    std::int64_t s = 0;
    for (std::int64_t v : l) s += v;
    return s;
}

double adjacent_share(const std::list<std::int64_t>& l) {
    std::size_t near = 0, pairs = 0;
    const std::int64_t* prev = nullptr;
    for (const std::int64_t& v : l) {
        if (prev && std::llabs(reinterpret_cast<const char*>(&v) - reinterpret_cast<const char*>(prev)) <= 64) ++near;
        prev = &v;
        ++pairs;
    }
    return static_cast<double>(near) / static_cast<double>(pairs - 1);
}

double ns_per_node(const std::list<std::int64_t>& l, std::int64_t expect) {
    auto t0 = std::chrono::steady_clock::now();
    for (int r = 0; r < 5; ++r)
        if (sum(l) != expect) std::abort();
    std::chrono::duration<double, std::nano> dt = std::chrono::steady_clock::now() - t0;
    return dt.count() / 5 / static_cast<double>(l.size());
}

int main(int argc, char** argv) {
    const std::int64_t n = argc > 1 ? std::atoll(argv[1]) : 2000000;
    std::vector<std::int64_t> values(static_cast<std::size_t>(n));
    std::iota(values.begin(), values.end(), 0);

    std::list<std::int64_t> a(values.begin(), values.end());

    std::shuffle(values.begin(), values.end(), std::mt19937_64(1));
    std::list<std::int64_t> b(values.begin(), values.end());
    b.sort();

    const std::int64_t expect = n * (n - 1) / 2;
    std::printf("%d\n", std::equal(a.begin(), a.end(), b.begin()) ? 1 : 0);
    std::printf("near neighbours: %.4f %.4f\n", adjacent_share(a), adjacent_share(b));
    std::printf("ns per node: %.2f %.2f\n", ns_per_node(a, expect), ns_per_node(b, expect));
}
