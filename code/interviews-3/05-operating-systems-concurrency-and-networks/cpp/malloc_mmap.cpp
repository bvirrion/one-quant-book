#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>

static const char* where(void* p) {
    auto a = reinterpret_cast<std::uintptr_t>(p);
    FILE* f = std::fopen("/proc/self/maps", "r");
    char line[512];
    const char* out = "unmapped";
    while (std::fgets(line, sizeof line, f)) {
        unsigned long lo, hi;
        if (std::sscanf(line, "%lx-%lx", &lo, &hi) == 2 && lo <= a && a < hi)
            out = std::strstr(line, "[heap]") ? "heap" : "mmap";
    }
    std::fclose(f);
    return out;
}

int main() {
    void* small = std::malloc(1024);
    void* big = std::malloc(1 << 20);
    std::printf("%s %s\n", where(small), where(big));
    std::free(big);
    std::printf("%s\n", where(big));
    void* again = std::malloc(1 << 20);
    std::printf("%s\n", where(again));
    std::free(again);
    std::free(small);
}
