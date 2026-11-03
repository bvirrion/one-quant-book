#include <cstdio>

struct Stats { long count; long sum; };

Stats* make_stats() { return new Stats; }

long average(const long* xs, int n) {
    Stats* s = make_stats();
    for (int i = 0; i < n; ++i) {
        s->count += 1;
        s->sum += xs[i];
    }
    const long out = s->sum / s->count;
    delete s;
    return out;
}

int main() {
    const long xs[] = {100, 200, 300};
    std::printf("%ld\n", average(xs, 3));
}
