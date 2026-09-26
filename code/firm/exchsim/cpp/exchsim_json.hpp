// A minimal JSON reader for the simulator's configuration files (objects, arrays, strings, integers, true,
// false, null). Enough for fixture_config.json and the server's --config; not a general-purpose parser.
#pragma once
#include <cctype>
#include <cstdint>
#include <map>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

namespace firm::exchsim::json {

struct Value {
    enum Kind { Null, Bool, Int, Str, Arr, Obj } kind = Null;
    bool b = false;
    std::int64_t i = 0;
    std::string s;
    std::vector<Value> a;
    std::map<std::string, Value> o;

    const Value& operator[](const std::string& k) const {
        auto it = o.find(k);
        if (it == o.end()) throw std::runtime_error("json: missing key " + k);
        return it->second;
    }
    bool has(const std::string& k) const { return kind == Obj && o.count(k) != 0; }
    std::int64_t get_int(const std::string& k, std::int64_t dflt) const { return has(k) ? (*this)[k].i : dflt; }
    std::string get_str(const std::string& k, const std::string& dflt) const { return has(k) ? (*this)[k].s : dflt; }
};

class Parser {
public:
    explicit Parser(const std::string& text) : t_(text) {}
    Value parse() {
        Value v = value();
        ws();
        if (p_ != t_.size()) throw std::runtime_error("json: trailing characters");
        return v;
    }

private:
    void ws() { while (p_ < t_.size() && std::isspace(static_cast<unsigned char>(t_[p_]))) ++p_; }
    char peek() { ws(); if (p_ >= t_.size()) throw std::runtime_error("json: unexpected end"); return t_[p_]; }
    void expect(char c) { if (peek() != c) throw std::runtime_error(std::string("json: expected ") + c); ++p_; }
    std::string str() {
        expect('"');
        std::string r;
        while (p_ < t_.size() && t_[p_] != '"') {
            if (t_[p_] == '\\') { ++p_; }
            r += t_[p_++];
        }
        expect('"');
        return r;
    }
    Value value() {
        Value v;
        const char c = peek();
        if (c == '{') {
            v.kind = Value::Obj;
            ++p_;
            if (peek() == '}') { ++p_; return v; }
            while (true) {
                std::string k = str();
                expect(':');
                v.o[k] = value();
                if (peek() == ',') { ++p_; continue; }
                expect('}');
                return v;
            }
        }
        if (c == '[') {
            v.kind = Value::Arr;
            ++p_;
            if (peek() == ']') { ++p_; return v; }
            while (true) {
                v.a.push_back(value());
                if (peek() == ',') { ++p_; continue; }
                expect(']');
                return v;
            }
        }
        if (c == '"') { v.kind = Value::Str; v.s = str(); return v; }
        if (t_.compare(p_, 4, "true") == 0) { v.kind = Value::Bool; v.b = true; p_ += 4; return v; }
        if (t_.compare(p_, 5, "false") == 0) { v.kind = Value::Bool; p_ += 5; return v; }
        if (t_.compare(p_, 4, "null") == 0) { p_ += 4; return v; }
        std::size_t used = 0;
        v.kind = Value::Int;
        v.i = std::stoll(t_.substr(p_), &used);
        p_ += used;
        return v;
    }
    const std::string& t_;
    std::size_t p_ = 0;
};

inline Value parse(const std::string& text) { return Parser(text).parse(); }

}  // namespace firm::exchsim::json
