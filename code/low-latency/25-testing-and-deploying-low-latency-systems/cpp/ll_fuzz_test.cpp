// Chapter 25: the firm's FIX parser under 200,000 mutated messages. Every input is copied into a buffer of exactly its
// size (so that a sanitiser would see any read past it); the parser must either reject the input or accept it with
// every field inside the buffer and a correct checksum. The golden messages themselves must parse.
#include "ll_fuzz.hpp"

#include <cstdio>
#include <map>
#include <memory>

int main() {
    const auto corpus = ll::fuzz::corpus("code/firm/fixengine/data/conversation.txt");
    int fails = 0;
    firm::fix::View v;
    for (const auto& m : corpus)
        if (v.parse(m.data(), m.size()) != firm::fix::Error::ok) ++fails;
    ll::fuzz::Mutator mut(1);
    std::map<int, int> errors;
    for (int it = 0; it < 200'000; ++it) {
        const std::string m = mut.mutate(corpus[mut.next() % corpus.size()]);
        std::unique_ptr<char[]> buf(new char[m.size() ? m.size() : 1]);
        std::memcpy(buf.get(), m.data(), m.size());
        const auto e = v.parse(buf.get(), m.size());
        ++errors[static_cast<int>(e)];
        if (e == firm::fix::Error::ok) {
            for (std::size_t i = 0; i < v.size(); ++i) {
                const auto val = v.value(i);
                if (val.data() < buf.get() || val.data() + val.size() > buf.get() + m.size()) ++fails;
            }
            unsigned c = 0;
            const auto ck = v.value(v.size() - 1);
            for (char d : ck) c = c * 10 + static_cast<unsigned>(d - '0');
            if (c != firm::fix::checksum(buf.get(), static_cast<std::size_t>(ck.data() - 3 - buf.get()))) ++fails;
        }
    }
    const char* names[] = {"ok", "framing", "tag", "order", "body_length", "checksum", "too_many_fields"};
    for (const auto& [e, n] : errors) std::printf("%s %d\n", names[e], n);
    std::printf(fails ? "FAIL\n" : "ok\n");
    return fails ? 1 : 0;
}
