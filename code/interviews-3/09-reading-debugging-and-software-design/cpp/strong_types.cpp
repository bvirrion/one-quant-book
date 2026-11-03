#include <cstdio>

struct Price { long ticks; };
struct Qty { long lots; };

void send(Price price, Qty qty) {
    std::printf("%ld at %ld\n", qty.lots, price.ticks);
}

long cost_raw(long price, long qty) { return price * qty; }
long cost_typed(Price price, Qty qty) { return price.ticks * qty.lots; }

int main() {
    Price price{101};
    Qty qty{500};
    send(price, qty);
    std::printf("%ld %ld\n", cost_raw(101, 500), cost_typed(price, qty));
}
