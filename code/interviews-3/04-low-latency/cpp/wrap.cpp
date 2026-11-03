#include <cstdint>
#include <cstdio>

struct Ring {
    static constexpr std::uint32_t capacity = 1000;
    long slots[capacity] = {};
    std::uint32_t head = 0, tail = 0;

    bool push(long v) {
        if (tail - head == capacity) return false;
        slots[tail % capacity] = v;
        ++tail;
        return true;
    }
    bool pop(long& v) {
        if (tail == head) return false;
        v = slots[head % capacity];
        ++head;
        return true;
    }
};

int main() {
    Ring r;
    r.head = r.tail = 0xFFFFFFFFu - 399;
    for (long i = 0; i < 500; ++i) r.push(i);
    long v, expect = 0, wrong = 0;
    while (r.pop(v)) wrong += v != expect++;
    std::printf("%ld wrong of %ld\n", wrong, expect);
}
