// Chapter 14: records and columns give the same revaluation, element by element, and the FIX split finds every field.
#include "ll_simd.hpp"
#include "../../../firm/simdscan/cpp/firm_simdscan.hpp"

#include <cmath>
#include <cstdio>
#include <string>

using namespace ll::simd;

int main() {
    std::vector<OptionRow> rows;
    OptionColumns cols;
    make_book(10007, rows, cols);   // an odd size: the vector loop's remainder is exercised
    std::vector<double> a(rows.size()), b(rows.size());
    const Move m{1.25, 0.4, -1.0 / 365};
    revalue_rows(rows.data(), rows.size(), m, a.data());
    revalue_columns(cols, m, b.data());
    for (std::size_t i = 0; i < a.size(); ++i)
        if (std::fabs(a[i] - b[i]) > 1e-12 * (1 + std::fabs(a[i]))) return 1;
    const std::string fix = "8=FIX.4.4\x01" "35=D\x01" "55=ESZ6\x01" "54=1\x01" "38=5\x01" "44=5723.25\x01" "10=123\x01";
    std::uint32_t pos[16];
    const std::size_t k = firm::simdscan::positions(fix.data(), fix.size(), '\x01', pos, 16);
    if (k != 7 || pos[6] != fix.size() - 1) return 2;
    std::int64_t price = 0;
    const std::size_t start = fix.find("44=") + 3;
    if (!firm::simdscan::parse_fixed(fix.data() + start, pos[5] - start, 4, price) || price != 57232500) return 3;
    std::printf("records and columns agree on %zu options; %zu fields; price %lld\n", a.size(), k,
                static_cast<long long>(price));
    return 0;
}
