#include <iostream>
#include <memory>

struct Order {
    int id = 7;
    ~Order() { std::cout << "gone\n"; }
};

int main() {
    Order* raw = new Order;
    std::shared_ptr<Order> a(raw);
    std::shared_ptr<Order> b(raw);
    std::cout << a.use_count() << " " << b.use_count() << "\n";
}
