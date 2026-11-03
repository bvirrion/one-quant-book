#include <iostream>
#include <memory>

struct Node {
    std::shared_ptr<Node> next;
    std::weak_ptr<Node> prev;
    ~Node() { std::cout << "freed\n"; }
};

int main() {
    std::weak_ptr<Node> watch;
    {
        auto a = std::make_shared<Node>();
        auto b = std::make_shared<Node>();
        a->next = b;
        b->prev = a;
        watch = a;
        std::cout << a.use_count() << " " << b.use_count() << "\n";
        if (auto p = b->prev.lock()) std::cout << "alive " << p.use_count() << "\n";
    }
    std::cout << watch.expired() << " " << (watch.lock() == nullptr) << "\n";
}
