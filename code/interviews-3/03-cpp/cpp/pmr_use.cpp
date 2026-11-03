#include <cstdlib>
#include <iostream>
#include <memory_resource>
#include <new>
#include <string>
#include <vector>

static long news = 0;
[[gnu::noinline]] void* operator new(std::size_t n) {
    ++news;
    if (void* p = std::malloc(n)) return p;
    throw std::bad_alloc{};
}
[[gnu::noinline]] void operator delete(void* p) noexcept { std::free(p); }
[[gnu::noinline]] void operator delete(void* p, std::size_t) noexcept { std::free(p); }

namespace pmr = std::pmr;

struct Counting : pmr::memory_resource {
    pmr::memory_resource* up;
    long bytes = 0;
    explicit Counting(pmr::memory_resource* u) : up(u) {}
    void* do_allocate(std::size_t n, std::size_t a) override {
        bytes += n;
        return up->allocate(n, a);
    }
    void do_deallocate(void*, std::size_t, std::size_t) override {}
    bool do_is_equal(const memory_resource& o) const noexcept override {
        return this == &o;
    }
};
long used(bool reserve) {
    alignas(64) char buf[4096];
    pmr::monotonic_buffer_resource mono(buf, sizeof buf, pmr::null_memory_resource());
    Counting count(&mono);
    pmr::vector<int> v(&count);
    if (reserve) v.reserve(100);
    for (int i = 0; i < 100; ++i) v.push_back(i);
    return count.bytes;
}
int main() {
    std::cout << used(false) << " " << used(true) << "\n";
    long before = news;
    {
        alignas(64) char buf[8192];
        pmr::monotonic_buffer_resource mono(buf, sizeof buf, pmr::null_memory_resource());
        pmr::vector<pmr::string> rows(&mono);
        rows.emplace_back(100, 'x');
        rows.emplace_back(100, 'y');
        bool same = rows[0].get_allocator().resource() == &mono;
        std::cout << same << " " << news - before << "\n";
    }
    alignas(64) char tiny[64];
    pmr::monotonic_buffer_resource mono(tiny, sizeof tiny, pmr::null_memory_resource());
    pmr::vector<int> v(&mono);
    try { v.resize(1000); } catch (const std::bad_alloc&) { std::cout << "bad_alloc\n"; }
}
