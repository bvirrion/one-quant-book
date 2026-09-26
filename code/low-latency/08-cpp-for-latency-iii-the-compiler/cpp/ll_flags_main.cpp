// Chapter 8 flag benchmark: decode Book 1's sample `passes` times, calling ll::flags::handle for every message.
// Prints the checksum on line 1 and ns per message on line 2 (the contract of firm.flagbench).
#include <chrono>
#include <cstdio>
#include <fstream>
#include <iterator>
#include <string>
#include <vector>

#include "ll_handle.hpp"

int main(int argc, char** argv) {
    const int passes = argc > 1 ? std::stoi(argv[1]) : 300;
    std::ifstream f("code/firm/feed/data/sample.itch", std::ios::binary);
    const std::vector<std::uint8_t> data{std::istreambuf_iterator<char>(f), std::istreambuf_iterator<char>()};
    ll::flags::Stats s;
    const auto t0 = std::chrono::steady_clock::now();
    for (int p = 0; p < passes; ++p) firm::feed::decode(data, [&](const firm::feed::Msg& m) { ll::flags::handle(m, s); });
    const double ns = std::chrono::duration<double, std::nano>(std::chrono::steady_clock::now() - t0).count();
    std::printf("%llu %llu %llu %llx\n%.3f\n", static_cast<unsigned long long>(s.msgs), static_cast<unsigned long long>(s.shares),
                static_cast<unsigned long long>(s.notional), static_cast<unsigned long long>(s.hash), ns / static_cast<double>(s.msgs));
    return 0;
}
