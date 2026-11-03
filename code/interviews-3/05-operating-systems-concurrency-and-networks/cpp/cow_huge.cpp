// Not printed. Copy-on-write over a range that really has huge pages: the answer's claim about them.
#include <cstdint>
#include <cstdio>
#include <sys/mman.h>
#include <sys/resource.h>
#include <sys/wait.h>
#include <unistd.h>

static long minor_faults() {
    rusage u;
    getrusage(RUSAGE_SELF, &u);
    return u.ru_minflt;
}

static long huge_kb() {
    std::FILE* f = std::fopen("/proc/self/smaps", "r");
    char line[256];
    long total = 0, v = 0;
    while (f && std::fgets(line, sizeof line, f))
        if (std::sscanf(line, "AnonHugePages: %ld", &v) == 1) total += v;
    if (f) std::fclose(f);
    return total;
}

int main() {
    const std::size_t page = 4096, n = 2000, huge = 2u << 20;
    int rw = PROT_READ | PROT_WRITE, flags = MAP_PRIVATE | MAP_ANONYMOUS;
    void* raw = mmap(nullptr, n * page + huge, rw, flags, -1, 0);
    auto start = (reinterpret_cast<std::uintptr_t>(raw) + huge - 1) & ~std::uintptr_t(huge - 1);
    madvise(reinterpret_cast<void*>(start), n * page, MADV_HUGEPAGE);
    auto* p = reinterpret_cast<volatile char*>(start);
    long t = minor_faults();
    for (std::size_t i = 0; i < n; ++i) p[i * page] = 1;
    std::printf("first touch %ld\nhuge kB %ld\n", minor_faults() - t, huge_kb());
    std::fflush(stdout);
    pid_t pid = fork();
    if (pid == 0) {
        long t0 = minor_faults();
        long sum = 0;
        for (std::size_t i = 0; i < n; ++i) sum += p[i * page];
        long t1 = minor_faults();
        for (std::size_t i = 0; i < n; ++i) p[i * page] = 2;
        long t2 = minor_faults();
        std::printf("child sum %ld read %ld write %ld\n", sum, t1 - t0, t2 - t1);
        std::fflush(stdout);
        _exit(0);
    }
    waitpid(pid, nullptr, 0);
}
