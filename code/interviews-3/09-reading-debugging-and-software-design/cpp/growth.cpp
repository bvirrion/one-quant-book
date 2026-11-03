#include <cstdio>
#include <map>

struct Order { long id; char pad[120]; };

std::map<long, Order> done;              // finished orders, kept "for the audit"

void on_fill(long id) { done.emplace(id, Order{id, {}}); }

int main() {
    for (long id = 0; id < 100000; ++id) on_fill(id);
    std::printf("%zu\n", done.size());
}
