#include <cstdio>
#include <memory>
#include <string>

struct Order {
    virtual long qty() const { return 0; }
    ~Order() { std::puts("~Order"); }
};

struct LimitOrder : Order {
    std::string tag = "a tag too long for the small-string buffer";
    long qty() const override { return 100; }
    ~LimitOrder() { std::puts("~LimitOrder"); }
};

int main() {
    std::unique_ptr<Order> p = std::make_unique<LimitOrder>();
    std::printf("%ld\n", p->qty());
}
