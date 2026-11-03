#include <cstddef>
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

int main() {
    const std::size_t page = 4096, n = 2000;
    int rw = PROT_READ | PROT_WRITE, flags = MAP_PRIVATE | MAP_ANONYMOUS;
    void* raw = mmap(nullptr, n * page, rw, flags, -1, 0);
    madvise(raw, n * page, MADV_NOHUGEPAGE);
    auto* p = static_cast<volatile char*>(raw);
    for (std::size_t i = 0; i < n; ++i) p[i * page] = 1;
    std::fflush(stdout);
    pid_t pid = fork();
    if (pid == 0) {
        long t0 = minor_faults();
        long sum = 0;
        for (std::size_t i = 0; i < n; ++i) sum += p[i * page];
        long t1 = minor_faults();
        for (std::size_t i = 0; i < n; ++i) p[i * page] = 2;
        long t2 = minor_faults();
        std::printf("child %d at %p: sum %ld, read faults %ld, write faults %ld\n",
                    p[0], raw, sum, t1 - t0, t2 - t1);
        std::fflush(stdout);
        _exit(0);
    }
    waitpid(pid, nullptr, 0);
    std::printf("parent %d at %p\n", p[0], raw);
}
