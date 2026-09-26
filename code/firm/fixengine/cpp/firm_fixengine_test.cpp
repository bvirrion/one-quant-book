// firm.fixengine (C++20): the published example's body length and checksum, corruptions caught, framing, the
// builder's bytes equal to the Python reference's, and the golden conversation's trace reproduced line for line.
#include "firm_fixengine.hpp"

#include <fstream>
#include <iostream>
#include <sstream>

using namespace firm::fix;

static int fails = 0;
#define CHECK(c) do { if (!(c)) { std::printf("FAIL line %d: %s\n", __LINE__, #c); ++fails; } } while (0)

static std::string soh(std::string s) {
    for (auto& c : s)
        if (c == '|') c = SOH;
    return s;
}

static std::vector<std::string> lines(const char* path) {
    std::ifstream f(path);
    std::vector<std::string> out;
    for (std::string l; std::getline(f, l);) out.push_back(l);
    return out;
}

int main() {
    const std::string ex = soh(lines("code/firm/fixengine/data/wikipedia_example.fix").at(0));
    View v;
    CHECK(v.parse(ex.data(), ex.size()) == Error::ok);
    CHECK(v.get(9) == "65" && v.get(10) == "062" && v.msg_type() == "A" && v.seq() == 177 && v.size() == 10);
    std::string bad = ex;
    bad[ex.find("SERVER")] = 'X';
    CHECK(v.parse(bad.data(), bad.size()) == Error::checksum);
    bad = ex;
    bad.replace(ex.find("9=65"), 4, "9=64");
    CHECK(v.parse(bad.data(), bad.size()) == Error::body_length);

    Builder b;
    const std::string built(b.start("D", 2, "FIRM", "BROKER", 52201000)
                                .add(11, "ORD1").add(55, "ESZ6").add(54, "1").add(38, std::int64_t{5}).finish());
    CHECK(v.parse(built.data(), built.size()) == Error::ok && v.get(52) == "20260925-14:30:01.000");
    Error err;
    const std::string two = built + built;
    CHECK(frame(two.data(), two.size(), err) == built.size() && err == Error::ok);
    CHECK(frame(two.data(), built.size() - 1, err) == 0 && err == Error::ok);
    CHECK(frame("XX=1\x01", 5, err) == 0 && err == Error::framing);

    // The golden conversation.
    Session s("FIRM", "BROKER", 30);
    for (const auto& line : lines("code/firm/fixengine/data/conversation.txt")) {
        if (line.empty() || line[0] == '#') continue;
        std::istringstream in(line);
        std::int64_t now;
        std::string verb, rest;
        in >> now >> verb;
        std::getline(in, rest);
        if (!rest.empty() && rest[0] == ' ') rest.erase(0, 1);
        if (verb == "logon") s.logon(now);
        else if (verb == "send") s.send(rest.substr(0, rest.find(' ')), soh(rest.substr(rest.find(' ') + 1) + "|"), now);
        else if (verb == "in") {
            s.trace.push_back(std::to_string(now) + " in " + rest);
            const std::string m = soh(rest);
            CHECK(s.on_bytes(m.data(), m.size(), now) == Error::ok);
        } else if (verb == "timer") s.on_timer(now);
        else if (verb == "logout") s.logout(now);
    }
    const auto want = lines("code/firm/fixengine/data/expected_trace.txt");
    CHECK(s.trace.size() == want.size());
    for (std::size_t i = 0; i < std::min(want.size(), s.trace.size()); ++i)
        if (s.trace[i] != want[i]) {
            std::printf("trace line %zu differs:\n  got  %s\n  want %s\n", i + 1, s.trace[i].c_str(), want[i].c_str());
            ++fails;
            break;
        }
    CHECK(s.state == "disconnected" && s.next_in == 10 && s.next_out == 8);
    std::printf("%s (%zu trace lines)\n", fails ? "FAILED" : "golden conversation reproduced", s.trace.size());
    return fails ? 1 : 0;
}
