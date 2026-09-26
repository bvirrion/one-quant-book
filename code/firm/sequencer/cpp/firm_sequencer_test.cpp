// firm.sequencer (C++20): a replica replays the fixture's failover journal to the states of data/expected.txt (hash,
// position, open orders, unacknowledged keys) at every listed prefix; two replicas agree entry by entry; a writer from a
// fenced epoch cannot append.
#include "firm_sequencer.hpp"

#include <fstream>
#include <sstream>
#include <string>

using namespace firm::seq;

int main() {
    int fails = 0;
    std::ifstream jf("code/firm/sequencer/data/journal.txt");
    std::vector<Entry> entries;
    for (std::string line; std::getline(jf, line);) entries.push_back(parse(line));
    std::ifstream ef("code/firm/sequencer/data/expected.txt");
    std::map<std::int64_t, std::string> want;
    for (std::string line; std::getline(ef, line);) {
        std::istringstream in(line);
        std::string w;
        std::int64_t n;
        in >> w >> n;
        want[n] = line;
    }
    Replica a, b;
    for (const Entry& e : entries) {
        a.apply(e);
        b.apply(e);
        if (a.hash != b.hash) ++fails;
        auto it = want.find(e.seq);
        if (it == want.end()) continue;
        char h[17];
        std::snprintf(h, sizeof h, "%016llx", static_cast<unsigned long long>(a.hash));
        std::string keys;
        for (const auto& [s, i] : a.unacknowledged()) keys += (keys.empty() ? "" : ",") + std::to_string(s) + "." + std::to_string(i);
        const std::string got = "prefix " + std::to_string(e.seq) + " " + h + " " + std::to_string(a.position) + " " +
                                std::to_string(a.open.size()) + " " + (keys.empty() ? "-" : keys);
        std::printf("%s\n", got.c_str());
        if (got != it->second) std::printf("  expected %s\n", it->second.c_str()), ++fails;
    }
    // fencing: once the backup has raised the epoch, the old primary's append is refused
    Journal j;
    j.append(Entry{1, 0, 'M', 1'000'000});
    j.fence(2);
    bool refused = false;
    try {
        j.append(Entry{1, 0, 'M', 1'000'100});
    } catch (const std::runtime_error&) {
        refused = true;
    }
    if (!refused || j.append(Entry{2, 0, 'M', 1'000'200}) != 2) std::printf("fencing failed\n"), ++fails;
    std::printf(fails ? "FAIL\n" : "ok\n");
    return fails ? 1 : 0;
}
