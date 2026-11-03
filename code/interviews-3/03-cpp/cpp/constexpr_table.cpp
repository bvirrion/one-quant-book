#include <array>
#include <cstdint>
#include <iostream>

constexpr std::array<std::int64_t, 19> make_powers() {
    std::array<std::int64_t, 19> t{};
    std::int64_t x = 1;
    for (std::size_t i = 0; i < t.size(); ++i) {
        t[i] = x;
        if (i + 1 < t.size()) x *= 10;
    }
    return t;
}

constexpr auto powers = make_powers();
static_assert(powers[18] == 1'000'000'000'000'000'000);

constexpr int twice(int x) { return 2 * x; }
consteval int always(int x) { return 2 * x; }

int main(int argc, char**) {
    constexpr int a = twice(21);
    int b = twice(argc);
    int c = always(21);
    std::cout << a << " " << b << " " << c << " " << powers[3] << "\n";
    // try each line here
}
