// Chapter 15 benchmark: parse and build FIX execution reports.
//   zero-copy View (firm.fixengine, SOH found with firm.simdscan), std::map parser, Builder, std::string concatenation.
// Output: method,ns_per_msg
#include <cstdio>
#include <string>
#include <vector>

#include "firm_fixengine.hpp"
#include "firm_ubench.hpp"
#include "ll_fixparse.hpp"

using namespace firm::fix;
using namespace firm::ubench;

static std::vector<std::string> reports(int n) {
    std::vector<std::string> out;
    Builder b;
    for (int i = 0; i < n; ++i) {
        const std::int64_t qty = 1 + i % 9, done = i % 10 == 0 ? qty : qty / 2;
        const std::string px = "5723." + std::to_string(10 + i % 80);
        out.emplace_back(b.start("8", 1000 + i, "BROKER", "FIRM", 52'200'000 + i)
                             .add(37, "X" + std::to_string(700000 + i)).add(11, "ORD" + std::to_string(i))
                             .add(17, "E" + std::to_string(900000 + i)).add(150, "F").add(39, done == qty ? "2" : "1")
                             .add(55, "ESZ6").add(54, "1").add(38, qty).add(32, done).add(31, px)
                             .add(151, qty - done).add(14, done).add(6, px).add(60, "20260925-14:30:00.123456")
                             .finish());
    }
    return out;
}

template <class F>
static double per_msg(const Clock& clk, std::size_t n, F&& f) {
    std::vector<double> t;
    for (int rep = 0; rep < 41; ++rep) {
        const std::uint64_t a = tsc_start();
        for (std::size_t i = 0; i < n; ++i) f(i);
        const std::uint64_t b = rdtscp();
        if (rep > 0) t.push_back(clk.ns(b - a) / static_cast<double>(n));
    }
    return quantile(t, 0.5);
}

int main() {
    const Clock clk = Clock::calibrate();
    const auto msgs = reports(1000);
    std::size_t bytes = 0;
    for (const auto& m : msgs) bytes += m.size();
    std::uint64_t sink = 0;
    View v;
    const double view = per_msg(clk, msgs.size(), [&](std::size_t i) {
        v.parse(msgs[i].data(), msgs[i].size());
        sink += v.get(14).size();
    });
    const double map = per_msg(clk, msgs.size(), [&](std::size_t i) {
        const auto m = ll::fix::parse_map(msgs[i]);
        sink += m.at(14).size();
    });
    Builder b;
    const double build = per_msg(clk, msgs.size(), [&](std::size_t i) {
        const auto s = b.start("D", static_cast<std::int64_t>(i), "FIRM", "BROKER", 52'200'000)
                           .add(11, "ORD1").add(55, "ESZ6").add(54, "1").add(38, std::int64_t{5}).add(40, "2")
                           .add(44, "5723.25").add(59, "0").finish();
        sink += s.size();
    });
    const double concat = per_msg(clk, msgs.size(), [&](std::size_t i) {
        std::string body = "35=D\x01" "49=FIRM\x01" "56=BROKER\x01" "34=" + std::to_string(i) + "\x01" +
                           "52=" + sending_time(52'200'000) + "\x01" + "11=ORD1\x01" "55=ESZ6\x01" "54=1\x01" +
                           "38=" + std::to_string(5) + "\x01" + "40=2\x01" "44=5723.25\x01" "59=0\x01";
        std::string m = "8=FIX.4.4\x01" "9=" + std::to_string(body.size()) + "\x01" + body;
        char ck[8];
        std::snprintf(ck, sizeof ck, "%03u", checksum(m.data(), m.size()));
        m += std::string("10=") + ck + "\x01";
        sink += m.size();
    });
    do_not_optimize(sink);
    std::printf("method,ns_per_msg\nview,%.1f\nmap,%.1f\nbuilder,%.1f\nconcat,%.1f\nbytes,%.1f\n", view, map, build,
                concat, static_cast<double>(bytes) / static_cast<double>(msgs.size()));
    return 0;
}
