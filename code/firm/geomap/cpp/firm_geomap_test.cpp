// Checks the C++20 geodesic against Karney's test set (data/geodtest_subset.txt): every distance within 1 mm.
#include <cmath>
#include <cstdio>
#include <fstream>
#include <string>

#include "firm_geomap.hpp"

int main() {
    const std::string here = __FILE__;
    std::ifstream in(here.substr(0, here.rfind('/') + 1) + "../data/geodtest_subset.txt");
    if (!in) { std::puts("missing fixture"); return 1; }
    double lat1, lon1, lat2, lon2, s, worst = 0;
    int n = 0;
    while (in >> lat1 >> lon1 >> lat2 >> lon2 >> s) {
        worst = std::fmax(worst, std::fabs(firm::geomap::geodesic_m(lat1, lon1, lat2, lon2) - s));
        ++n;
    }
    std::printf("geomap: %d geodesics, worst error %.3g m\n", n, worst);
    return n > 200 && worst < 1e-4 ? 0 : 1;
}
