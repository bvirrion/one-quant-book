// Chapter 15: the naive parser the zero-copy View is compared with -- every field copied into a std::map.
#pragma once
#include <map>
#include <string>
#include <string_view>

namespace ll::fix {

// Split on SOH, convert each tag with std::stoi and copy each value into a map node: several allocations per field.
inline std::map<int, std::string> parse_map(std::string_view m) {
    std::map<int, std::string> out;
    std::size_t start = 0;
    while (start < m.size()) {
        const std::size_t end = m.find('\x01', start);
        const std::size_t eq = m.find('=', start);
        out[std::stoi(std::string(m.substr(start, eq - start)))] = std::string(m.substr(eq + 1, end - eq - 1));
        start = end + 1;
    }
    return out;
}

}  // namespace ll::fix
