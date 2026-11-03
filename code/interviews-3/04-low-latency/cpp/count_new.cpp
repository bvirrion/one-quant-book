#include <cstdio>
#include <cstdlib>
#include <functional>
#include <map>
#include <memory>
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
volatile long sink;

template <class F>
void show(const char* name, F f) {
    long before = news;
    f();
    std::printf("%-12s %ld\n", name, news - before);
}

int main() {
    using V = std::vector<int>;
    show("string 15", [] { std::string s(15, 'x'); sink = s[0]; });
    show("string 16", [] { std::string s(16, 'x'); sink = s[0]; });
    show("push 1000", [] {
        V v; for (int i = 0; i < 1000; ++i) v.push_back(i); sink = v[9]; });
    show("reserved", [] {
        V v; v.reserve(1000);
        for (int i = 0; i < 1000; ++i) v.push_back(i);
        sink = v[9]; });
    show("function 16", [] {
        long a = 1, b = 2;
        std::function<long()> f = [a, b] { return a + b; }; sink = f(); });
    show("function 24", [] {
        long a = 1, b = 2, c = 3;
        std::function<long()> f = [a, b, c] { return a + b + c; }; sink = f(); });
    show("shared new", [] { std::shared_ptr<long> p(new long(1)); sink = *p; });
    show("make_shared", [] { auto p = std::make_shared<long>(1); sink = *p; });
    show("map 10", [] {
        std::map<int, int> m; for (int i = 0; i < 10; ++i) m[i] = i; sink = m[3]; });
}
