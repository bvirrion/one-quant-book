// firm.arena allocation counter: replaces the global operator new/delete to count heap allocations.
// Include in exactly one translation unit (a test or a benchmark), then read firm::arena::allocations().
#pragma once
#include <atomic>
#include <cstdlib>
#include <new>

namespace firm::arena {
inline std::atomic<unsigned long long> g_allocations{0};
inline unsigned long long allocations() { return g_allocations.load(std::memory_order_relaxed); }
}  // namespace firm::arena

void* operator new(std::size_t n) {
    firm::arena::g_allocations.fetch_add(1, std::memory_order_relaxed);
    if (void* p = std::malloc(n ? n : 1)) return p;
    throw std::bad_alloc();
}
void* operator new[](std::size_t n) { return ::operator new(n); }
void operator delete(void* p) noexcept { std::free(p); }
void operator delete[](void* p) noexcept { std::free(p); }
void operator delete(void* p, std::size_t) noexcept { std::free(p); }
void operator delete[](void* p, std::size_t) noexcept { std::free(p); }
