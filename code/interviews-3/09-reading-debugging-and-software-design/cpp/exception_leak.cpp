#include <cstdio>
#include <stdexcept>
#include <string>

struct Order { long qty; std::string tag; };

void validate(const Order& o) {
    if (o.qty <= 0) throw std::invalid_argument("bad qty");
}

long handle(long qty) {
    Order* o = new Order{qty, "tag"};
    validate(*o);
    const long q = o->qty;
    delete o;
    return q;
}

int main() {
    long total = 0;
    for (long q : {100L, -1L, 200L}) {
        try {
            total += handle(q);
        } catch (const std::exception& e) {
            std::puts(e.what());
        }
    }
    std::printf("%ld\n", total);
}
