// Chapter 17: the naive JSON path the structural index is compared with -- a general recursive-descent parser that
// builds a tree of values (strings copied, maps and vectors allocated), then a depth update read from the tree with
// floating-point prices.
#pragma once
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <map>
#include <memory>
#include <string>
#include <string_view>
#include <vector>

namespace ll::naive {

struct Value {
    enum Kind { kNull, kNumber, kString, kArray, kObject } kind = kNull;
    double number = 0;
    std::string str;
    std::vector<Value> arr;
    std::map<std::string, Value> obj;
};

class Parser {
public:
    explicit Parser(std::string_view s) : s_(s) {}
    Value parse() {
        ws();
        Value v;
        if (s_[i_] == '{') {
            v.kind = Value::kObject;
            ++i_;
            ws();
            while (s_[i_] != '}') {
                std::string k = string();
                ws();
                ++i_;   // ':'
                v.obj.emplace(std::move(k), parse());
                ws();
                if (s_[i_] == ',') ++i_;
                ws();
            }
            ++i_;
        } else if (s_[i_] == '[') {
            v.kind = Value::kArray;
            ++i_;
            ws();
            while (s_[i_] != ']') {
                v.arr.push_back(parse());
                ws();
                if (s_[i_] == ',') ++i_;
                ws();
            }
            ++i_;
        } else if (s_[i_] == '"') {
            v.kind = Value::kString;
            v.str = string();
        } else {
            v.kind = Value::kNumber;
            const std::string num(s_.substr(i_, s_.find_first_of(",}]", i_) - i_));
            v.number = std::strtod(num.c_str(), nullptr);
            i_ += num.size();
        }
        return v;
    }

private:
    void ws() { while (i_ < s_.size() && (s_[i_] == ' ' || s_[i_] == '\n')) ++i_; }
    std::string string() {
        const std::size_t a = ++i_;
        while (s_[i_] != '"') ++i_;
        return std::string(s_.substr(a, i_++ - a));
    }
    std::string_view s_;
    std::size_t i_ = 0;
};

struct Depth {
    std::uint64_t event_time = 0, first = 0, last = 0;
    std::string symbol;
    std::vector<std::pair<std::int64_t, std::int64_t>> bids, asks;
};

inline Depth decode_depth(std::string_view text) {
    const Value v = Parser(text).parse();
    Depth d;
    d.event_time = static_cast<std::uint64_t>(v.obj.at("E").number);
    d.symbol = v.obj.at("s").str;
    d.first = static_cast<std::uint64_t>(v.obj.at("U").number);
    d.last = static_cast<std::uint64_t>(v.obj.at("u").number);
    for (const char* side : {"b", "a"})
        for (const auto& lv : v.obj.at(side).arr)
            (side[0] == 'b' ? d.bids : d.asks)
                .emplace_back(std::llround(std::strtod(lv.arr[0].str.c_str(), nullptr) * 1e8),
                              std::llround(std::strtod(lv.arr[1].str.c_str(), nullptr) * 1e8));
    return d;
}

}  // namespace ll::naive
