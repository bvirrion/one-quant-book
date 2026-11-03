#include <cstdio>
#include <cstdlib>
#include <memory>
#include <new>

static long frees = 0;
[[gnu::noinline]] void* operator new(std::size_t n) {
    if (void* p = std::malloc(n)) return p;
    throw std::bad_alloc{};
}
[[gnu::noinline]] void operator delete(void* p) noexcept { ++frees; std::free(p); }
[[gnu::noinline]] void operator delete(void* p, std::size_t) noexcept {
    ++frees;
    std::free(p);
}

struct Big {
    char bytes[1'000'000];
    ~Big() { std::puts("destroyed"); }
};

template <class Make>
void run(const char* name, Make make) {
    frees = 0;
    std::weak_ptr<Big> w;
    {
        std::shared_ptr<Big> s = make();
        w = s;
    }
    std::printf("%s: %ld frees while the weak_ptr lives\n", name, frees);
    w.reset();
    std::printf("%s: %ld frees after\n", name, frees);
}

int main() {
    run("new", [] { return std::shared_ptr<Big>(new Big); });
    run("make_shared", [] { return std::make_shared<Big>(); });
}
