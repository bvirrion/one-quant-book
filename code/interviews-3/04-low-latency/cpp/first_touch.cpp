#include <cstdio>
#include <cstdlib>
#include <sys/resource.h>
#include <vector>

long minor_faults() {
    rusage u{};
    getrusage(RUSAGE_SELF, &u);
    return u.ru_minflt;
}

void touch(volatile char* p, std::size_t n) {
    for (std::size_t i = 0; i < n; i += 4096) p[i] = 1;
}

int main() {
    const std::size_t n = 64u << 20;  // 64 MiB
    long t0 = minor_faults();
    char* m = static_cast<char*>(std::malloc(n));
    long t1 = minor_faults();
    touch(m, n);
    long t2 = minor_faults();
    touch(m, n);
    long t3 = minor_faults();
    std::printf("malloc %ld, first pass %ld, second pass %ld\n",
                t1 - t0, t2 - t1, t3 - t2);

    t0 = minor_faults();
    std::vector<char> v(n);
    t1 = minor_faults();
    touch(v.data(), n);
    t2 = minor_faults();
    std::printf("vector %ld, first pass %ld\n", t1 - t0, t2 - t1);
    std::free(m);
}
