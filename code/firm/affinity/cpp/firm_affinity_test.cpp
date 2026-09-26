// Acceptance test of firm.affinity, C++ side: read the example plan, pin a thread to an allowed CPU and verify.
#include "firm_affinity.hpp"

#include <cstdio>
#include <thread>

int main() {
    const auto plan = firm::affinity::read_plan("code/firm/affinity/data/plan_example.txt");
    if (plan.size() != 4 || plan.at("strategy") != 2) return 1;
    cpu_set_t allowed;
    sched_getaffinity(0, sizeof allowed, &allowed);
    int target = -1;
    for (int c = 0; c < CPU_SETSIZE && target < 0; ++c) if (CPU_ISSET(c, &allowed)) target = c;
    int got = -2;
    std::thread t([&] { got = firm::affinity::apply({{"feed", target}}, "feed"); });
    t.join();
    if (got != target || firm::affinity::apply(plan, "nosuch") != -1) return 1;
    std::puts("affinity ok");
    return 0;
}
