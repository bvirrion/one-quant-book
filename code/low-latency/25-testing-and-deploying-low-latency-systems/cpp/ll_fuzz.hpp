// Chapter 25: a small mutational fuzzer for FIX messages, and a parser with a classic bug to find.
//   Mutator     seeded from the golden messages of firm.fixengine; each input is one or two mutations of one of them:
//               a byte flipped, a digit changed, a byte inserted or deleted, a field duplicated, a tail cut off
//   parse_trusting  a checksum reader that believes the BodyLength field (9=) instead of the bytes it was given
#pragma once
#include <cstdint>
#include <cstring>
#include <fstream>
#include <string>
#include <vector>

#include "../../../firm/fixengine/cpp/firm_fixengine.hpp"

namespace ll::fuzz {

inline std::vector<std::string> corpus(const std::string& conversation) {
    std::vector<std::string> out;
    std::ifstream f(conversation);
    for (std::string line; std::getline(f, line);) {
        const auto p = line.find(" in ");
        if (line.empty() || line[0] == '#' || p == std::string::npos) continue;
        std::string m = line.substr(p + 4);
        for (char& c : m)
            if (c == '|') c = firm::fix::SOH;
        out.push_back(m);
    }
    return out;
}

class Mutator {
public:
    explicit Mutator(std::uint64_t seed) : s_(seed * 0x9E3779B97F4A7C15ULL + 1) {}
    std::uint64_t next() {  // xorshift64*
        s_ ^= s_ >> 12, s_ ^= s_ << 25, s_ ^= s_ >> 27;
        return s_ * 0x2545F4914F6CDD1DULL;
    }
    std::string mutate(std::string m) {
        const int rounds = 1 + static_cast<int>(next() % 2);
        for (int r = 0; r < rounds && !m.empty(); ++r) {
            const std::size_t i = next() % m.size();
            switch (next() % 6) {
                case 0: m[i] = static_cast<char>(m[i] ^ (1 << (next() % 8))); break;
                case 1: {  // change a digit: the numbers of FIX (lengths, sequence numbers, checksums) are its weak spot
                    std::size_t j = i;
                    while (j < m.size() && (m[j] < '0' || m[j] > '9')) ++j;
                    if (j < m.size()) m[j] = static_cast<char>('0' + next() % 10);
                    break;
                }
                case 2: m.insert(m.begin() + static_cast<long>(i), static_cast<char>(next() % 256)); break;
                case 3: m.erase(m.begin() + static_cast<long>(i)); break;
                case 4: {  // duplicate the field that contains i
                    const std::size_t a = m.rfind(firm::fix::SOH, i), b = m.find(firm::fix::SOH, i);
                    if (a != std::string::npos && b != std::string::npos) m.insert(b + 1, m.substr(a + 1, b - a));
                    break;
                }
                default: m.resize(i); break;
            }
        }
        return m;
    }

private:
    std::uint64_t s_;
};

// The bug: the checksum is read where BodyLength says it is, without checking that the message is that long.
inline int parse_trusting(const char* p, std::size_t n) {
    const char* a = static_cast<const char*>(std::memchr(p, firm::fix::SOH, n));
    if (!a || n < 4 || p[0] != '8') return -1;
    const std::size_t f = static_cast<std::size_t>(a - p) + 1;  // the BodyLength field
    if (f + 2 > n || p[f] != '9' || p[f + 1] != '=') return -1;
    std::size_t k = f + 2, declared = 0;
    while (k < n && p[k] >= '0' && p[k] <= '9')
        declared = declared * 10 + static_cast<std::size_t>(p[k++] - '0');
    if (k >= n || p[k] != firm::fix::SOH || declared > 4096) return -1;
    const char* ck = p + k + 1 + declared + 3;  // after "10=": never checked against n
    return (ck[0] - '0') * 100 + (ck[1] - '0') * 10 + (ck[2] - '0');
}

}  // namespace ll::fuzz
