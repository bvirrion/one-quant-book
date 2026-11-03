#include <atomic>

std::atomic<long> x;
long plain;

long load_relaxed() { return x.load(std::memory_order_relaxed); }
long load_acquire() { return x.load(std::memory_order_acquire); }
long load_seq_cst() { return x.load(std::memory_order_seq_cst); }
void store_relaxed(long v) { x.store(v, std::memory_order_relaxed); }
void store_release(long v) { x.store(v, std::memory_order_release); }
void store_seq_cst(long v) { x.store(v, std::memory_order_seq_cst); }
void add_relaxed() { x.fetch_add(1, std::memory_order_relaxed); }
void add_plain() { ++plain; }
