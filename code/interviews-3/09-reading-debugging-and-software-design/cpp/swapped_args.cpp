#include <cstdio>

void send(long price, long qty) {
    std::printf("%ld at %ld\n", qty, price);
}

int main() {
    long price = 101, qty = 500;
    send(qty, price);
}
