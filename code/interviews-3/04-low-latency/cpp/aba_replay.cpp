#include <atomic>
#include <cstdint>
#include <cstdio>

// A stack over a pool of four nodes, by index; -1 is empty. No threads: one schedule, replayed by hand.
struct Node { int next; bool in_use; };
Node pool[4];

// Untagged head: only the index.
std::atomic<int> head{-1};

int pop() {
    int n = head.load();
    int next = n < 0 ? -1 : pool[n].next;
    if (n >= 0 && head.compare_exchange_strong(n, next)) {
        pool[n].in_use = false;
        return n;
    }
    return -1;
}
void push(int i) {
    pool[i].next = head.load();
    pool[i].in_use = true;
    head.store(i);
}

// Tagged head: index in the low half, a counter bumped on every change in the high half.
std::atomic<std::uint64_t> tagged{0xFFFFFFFFu};
int index_of(std::uint64_t w) { return static_cast<int>(static_cast<std::uint32_t>(w)); }
std::uint64_t with(std::uint64_t old, int i) { return ((old >> 32) + 1) << 32 | static_cast<std::uint32_t>(i); }

int main() {
    push(2);  // C, the bottom
    push(1);  // B
    push(0);  // A, the top
    int a = head.load();     // thread 1 reads the top, A
    int b = pool[a].next;    // thread 1 reads A's next, B, and is suspended
    pop();                   // thread 2 pops A
    int freed = pop();       // thread 2 pops B: B is free now
    push(a);                 // thread 2 reuses A and pushes it back
    bool won = head.compare_exchange_strong(a, b);  // thread 1 resumes
    std::printf("untagged: cas %d, head %d, head in use %d, freed %d\n", won, head.load(),
                pool[head.load()].in_use, freed);

    tagged.store(with(0xFFFFFFFFu, 0));  // A on top, tag 1
    std::uint64_t seen = tagged.load();  // thread 1 reads the top
    tagged.store(with(tagged.load(), 1));  // thread 2: pop A, head B
    tagged.store(with(tagged.load(), 2));  // thread 2: pop B, head C
    tagged.store(with(tagged.load(), 0));  // thread 2: push A back
    bool same_index = index_of(tagged.load()) == index_of(seen);
    bool won2 = tagged.compare_exchange_strong(seen, with(seen, 1));
    std::printf("tagged: same index %d, cas %d\n", same_index, won2);
}
