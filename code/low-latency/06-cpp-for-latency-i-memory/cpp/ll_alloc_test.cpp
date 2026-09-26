// Chapter 6: count the heap allocations of one message in each handler (deterministic on a given standard library).
#include "ll_alloc.hpp"
#include "../../../firm/arena/cpp/firm_alloc_count.hpp"

#include <cstdio>

using namespace ll::alloc;

int main() {
    const Fill f[3] = {{100, 1}, {101, 2}, {102, 3}};
    NaiveHandler naive;
    FixedHandler fixed;
    naive.handle("ESZ6", "CLIENT-ORDER-0000001-A", f, 3);   // warm-up: first key
    fixed.handle("ESZ6", "CLIENT-ORDER-0000001-A", f, 3);
    auto a0 = firm::arena::allocations();
    naive.handle("ESZ6", "CLIENT-ORDER-0000002-A", f, 3);
    const auto naive_allocs = firm::arena::allocations() - a0;
    a0 = firm::arena::allocations();
    fixed.handle("ESZ6", "CLIENT-ORDER-0000002-A", f, 3);
    const auto fixed_allocs = firm::arena::allocations() - a0;
    std::printf("naive %llu, fixed %llu allocations per message\n", naive_allocs, fixed_allocs);
    if (fixed_allocs != 0 || naive_allocs != 9) return 1;  // 1 + 3 + 2 + 1 + 2
    std::string s;
    if (s.capacity() != 15) return 1;  // libstdc++'s inline buffer: 15 characters
    return 0;
}
