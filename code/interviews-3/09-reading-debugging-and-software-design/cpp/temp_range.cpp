#include <cstdio>
#include <vector>

class Snapshot {
public:
    Snapshot() : levels_{100, 200, 300} {}
    const std::vector<long>& levels() const { return levels_; }

private:
    std::vector<long> levels_;
};

Snapshot latest() { return Snapshot{}; }

int main() {
    long total = 0;
    for (long q : latest().levels()) total += q;
    std::printf("%ld\n", total);
}
