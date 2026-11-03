#include <iostream>
#include <memory>

struct Order : std::enable_shared_from_this<Order> {
    std::shared_ptr<Order> self() { return shared_from_this(); }
};

int main() {
    auto a = std::make_shared<Order>();
    auto b = a->self();
    std::cout << a.use_count() << " " << b.use_count() << "\n";
    Order plain;
    try {
        plain.self();
    } catch (const std::bad_weak_ptr&) {
        std::cout << "bad_weak_ptr\n";
    }
}
