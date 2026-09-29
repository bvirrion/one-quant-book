// firm.hwtrade Verilator testbench: beats from a stimulus file (one per cycle, "I" for an idle cycle), registers from
// the command line (thresh, max_qty, the cycle at which kill is set, -1 for never); prints "<cycle> O <id> <qty>
// <price>" for each order and "R <rejects>" at the end. tb/hwt_tb.sv prints the same lines.
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <string>
#include <vector>

#include "Vhwt_trigger.h"
#include "verilated.h"

struct Beat { bool idle; bool last; unsigned keep; std::uint64_t data; };

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);
    if (argc < 5) { std::puts("usage: sim stim thresh max_qty kill_at"); return 2; }
    std::vector<Beat> beats;
    std::ifstream s(argv[1]);
    std::string kind;
    while (s >> kind) {
        Beat b{kind == "I", false, 0, 0};
        if (!b.idle) { unsigned last = 0; s >> last >> std::hex >> b.keep >> b.data >> std::dec; b.last = last != 0; }
        beats.push_back(b);
    }
    const long kill_at = std::atol(argv[4]);
    Vhwt_trigger* m = new Vhwt_trigger;
    m->thresh = static_cast<std::uint32_t>(std::strtoul(argv[2], nullptr, 10));
    m->max_qty = static_cast<std::uint32_t>(std::strtoul(argv[3], nullptr, 10));
    m->kill = 0;
    m->rst = 1;
    for (int k = 0; k < 2; ++k) { m->clk = 0; m->eval(); m->clk = 1; m->eval(); }
    m->rst = 0;
    const long n = static_cast<long>(beats.size());
    for (long cycle = 0; cycle < n + 8; ++cycle) {
        const bool have = cycle < n && !beats[cycle].idle;
        m->in_valid = have;
        if (have) { m->in_last = beats[cycle].last; m->in_keep = beats[cycle].keep; m->in_data = beats[cycle].data; }
        m->kill = kill_at >= 0 && cycle >= kill_at;
        m->clk = 0;
        m->eval();
        m->clk = 1;
        m->eval();
        if (m->order_valid)
            std::printf("%ld O %u %u %u\n", cycle, m->order_id, m->order_qty, m->order_price);
    }
    std::printf("R %u\n", static_cast<unsigned>(m->rejects));
    m->final();
    delete m;
    return 0;
}
