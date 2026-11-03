#include <atomic>
#include <cstdio>
#include <thread>
#include <vector>

struct Node {
    long value;
    Node* next;
};

class Stack {
    std::atomic<Node*> head_{nullptr};

public:
    void push(long v) {
        Node* n = new Node{v, head_.load(std::memory_order_relaxed)};
        while (!head_.compare_exchange_weak(n->next, n, std::memory_order_release,
                                            std::memory_order_relaxed)) {
        }
    }
    bool pop(long& out) {
        Node* n = head_.load(std::memory_order_acquire);
        while (n && !head_.compare_exchange_weak(n, n->next,
                                                 std::memory_order_acquire)) {
        }
        if (!n) return false;
        out = n->value;
        delete n;
        return true;
    }
};

Stack stack;

int main() {
    std::vector<std::thread> pool;
    for (int t = 0; t < 4; ++t)
        pool.emplace_back([t] {
            long v;
            for (long i = 0; i < 100000; ++i) {
                stack.push(t * 1000000 + i);
                stack.pop(v);
            }
        });
    for (auto& th : pool) th.join();
    std::printf("done\n");
}
