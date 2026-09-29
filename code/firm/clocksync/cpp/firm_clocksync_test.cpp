// Reproduces the Python servo's outputs on data/fixture_servo.csv (offset, interval -> step, frequency).
#include <cmath>
#include <cstdio>
#include <fstream>
#include <string>

#include "firm_clocksync.hpp"

int main() {
    const std::string here = __FILE__;
    std::ifstream in(here.substr(0, here.rfind('/') + 1) + "../data/fixture_servo.csv");
    if (!in) { std::puts("missing fixture"); return 1; }
    std::string line;
    std::getline(in, line);
    firm::clocksync::Servo s;
    int n = 0, bad = 0;
    while (std::getline(in, line)) {
        double off = 0, itv = 0, step = 0, freq = 0;
        if (std::sscanf(line.c_str(), "%lf,%lf,%lf,%lf", &off, &itv, &step, &freq) != 4) continue;
        const double got = s.update(off, itv);
        if (std::fabs(got - step) > 1e-6 * (1 + std::fabs(step)) || std::fabs(s.freq_ppb - freq) > 1e-6 * (1 + std::fabs(freq)))
            ++bad;
        ++n;
    }
    std::printf("clocksync servo: %d updates, %d mismatches\n", n, bad);
    return bad == 0 && n > 0 ? 0 : 1;
}
