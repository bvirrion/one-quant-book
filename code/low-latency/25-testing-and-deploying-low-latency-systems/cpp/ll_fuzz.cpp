// Chapter 25: the fuzzer as a program, built with AddressSanitizer and UndefinedBehaviorSanitizer by bench_fuzz.py.
//   ll_fuzz real <iterations> <seed>   the firm's parser: prints "real,<iterations>,<accepted>" (a crash would abort)
//   ll_fuzz trusting <seed>           the parser that trusts BodyLength: runs until the sanitiser stops it; the death
//                                     callback prints "trusting,<seed>,<iteration of the first bad read>"
#include <sanitizer/common_interface_defs.h>

#include <cstdio>
#include <cstdlib>
#include <memory>
#include <string>

#include "ll_fuzz.hpp"

static long g_iter = 0, g_seed = 0;

static void on_death() {
    std::printf("trusting,%ld,%ld\n", g_seed, g_iter);
    std::fflush(stdout);
}

int main(int argc, char** argv) {
    const std::string mode = argc > 1 ? argv[1] : "real";
    const auto corpus = ll::fuzz::corpus("code/firm/fixengine/data/conversation.txt");
    g_seed = std::atol(mode == "real" ? argv[3] : argv[2]);
    ll::fuzz::Mutator mut(static_cast<std::uint64_t>(g_seed));
    if (mode == "real") {
        const long n = std::atol(argv[2]);
        long accepted = 0;
        firm::fix::View v;
        for (g_iter = 0; g_iter < n; ++g_iter) {
            const std::string m = mut.mutate(corpus[mut.next() % corpus.size()]);
            std::unique_ptr<char[]> buf(new char[m.size() ? m.size() : 1]);
            std::memcpy(buf.get(), m.data(), m.size());
            accepted += v.parse(buf.get(), m.size()) == firm::fix::Error::ok;
        }
        std::printf("real,%ld,%ld\n", n, accepted);
        return 0;
    }
    __sanitizer_set_death_callback(on_death);
    for (g_iter = 1; g_iter < 100'000'000; ++g_iter) {
        const std::string m = mut.mutate(corpus[mut.next() % corpus.size()]);
        std::unique_ptr<char[]> buf(new char[m.size() ? m.size() : 1]);
        std::memcpy(buf.get(), m.data(), m.size());
        volatile int c = ll::fuzz::parse_trusting(buf.get(), m.size());
        (void)c;
    }
    std::printf("trusting,%ld,none\n", g_seed);
    return 0;
}
