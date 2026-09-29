// firm.hdlkit Verilator testbench for hdk_top: drives beats from a stimulus file, out_ready from a pattern file, and
// prints one line per event: "<cycle> I" (a beat accepted), "<cycle> F <hex>" (field), "<cycle> C <hex>" (CRC),
// "<cycle> M <0|1>" (comparison). The Icarus testbench (hdk_tb.sv) prints the same lines for the same inputs.
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

#include "Vhdk_top.h"
#include "verilated.h"

struct Beat { bool idle; bool last; unsigned keep; std::uint64_t data; };

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);
    if (argc < 4) { std::puts("usage: sim stim ready thresh_hex"); return 2; }
    std::vector<Beat> beats;
    std::ifstream s(argv[1]);
    std::string kind;
    while (s >> kind) {
        Beat b{kind == "I", false, 0, 0};
        if (!b.idle) { unsigned last = 0; s >> last >> std::hex >> b.keep >> b.data >> std::dec; b.last = last != 0; }
        beats.push_back(b);
    }
    std::vector<int> ready;
    std::ifstream r(argv[2]);
    int x = 0;
    while (r >> x) ready.push_back(x);
    const std::uint64_t thresh = std::strtoull(argv[3], nullptr, 16);
    Vhdk_top* m = new Vhdk_top;
    m->thresh = thresh;
    m->rst = 1;
    for (int k = 0; k < 2; ++k) { m->clk = 0; m->eval(); m->clk = 1; m->eval(); }
    m->rst = 0;
    std::size_t next = 0;
    for (long cycle = 0; cycle < static_cast<long>(beats.size()) * 4 + 64; ++cycle) {
        const bool idle_now = next < beats.size() && beats[next].idle;   // an idle line is one idle cycle
        const bool have = next < beats.size() && !idle_now;
        m->in_valid = have;
        if (have) { m->in_last = beats[next].last; m->in_keep = beats[next].keep; m->in_data = beats[next].data; }
        m->out_ready = ready[cycle % ready.size()];
        m->clk = 0;
        m->eval();
        const bool accepted = have && m->in_ready;
        m->clk = 1;
        m->eval();
        if (accepted) { std::printf("%ld I\n", cycle); ++next; }
        if (idle_now) ++next;
        if (m->field_valid) std::printf("%ld F %016llx\n", cycle, static_cast<unsigned long long>(m->field));
        if (m->crc_valid) std::printf("%ld C %08x\n", cycle, static_cast<unsigned>(m->crc));
        if (m->cmp_valid) std::printf("%ld M %d\n", cycle, static_cast<int>(m->cmp_le));
    }
    m->final();
    delete m;
    return 0;
}
