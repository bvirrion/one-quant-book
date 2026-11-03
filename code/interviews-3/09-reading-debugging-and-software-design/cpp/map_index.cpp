#include <cstdio>
#include <map>
#include <string>

std::map<std::string, long> limits{{"AAA", 1000}};

bool allowed(const std::string& symbol, long qty) {
    return qty <= limits[symbol];
}

int main() {
    std::printf("%d\n", allowed("AAA", 500));
    std::printf("%d\n", allowed("BBB", 0));
    std::printf("%zu\n", limits.size());
}
