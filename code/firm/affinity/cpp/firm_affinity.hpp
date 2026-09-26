// firm.affinity -- pin threads by role (build of One Quant Book 13, chapter 9), C++20 twin of the Rust crate.
// A plan file (written by firm_coreplan.write_plan) maps roles to CPUs, one "role cpu" per line; '#' starts a comment.
#pragma once
#include <pthread.h>
#include <sched.h>

#include <fstream>
#include <map>
#include <sstream>
#include <string>

namespace firm::affinity {

inline std::map<std::string, int> read_plan(const std::string& path) {
    std::map<std::string, int> out;
    std::ifstream f(path);
    std::string line;
    while (std::getline(f, line)) {
        if (line.empty() || line[0] == '#') continue;
        std::istringstream ss(line);
        std::string role;
        int cpu = -1;
        if (ss >> role >> cpu) out[role] = cpu;
    }
    return out;
}

// Pin the calling thread to one CPU; false if the kernel refused (CPU absent or not allowed).
inline bool pin_current(int cpu) {
    cpu_set_t s;
    CPU_ZERO(&s);
    CPU_SET(cpu, &s);
    return pthread_setaffinity_np(pthread_self(), sizeof s, &s) == 0;
}

inline int current_cpu() { return sched_getcpu(); }

// Name the thread (15 characters at most on Linux) so that top, perf and /proc show its role.
inline bool name_current(const std::string& name) { return pthread_setname_np(pthread_self(), name.substr(0, 15).c_str()) == 0; }

// Pin and name the calling thread as `role` from the plan; returns the CPU, or -1 if the role is absent or pinning failed.
inline int apply(const std::map<std::string, int>& plan, const std::string& role) {
    const auto it = plan.find(role);
    if (it == plan.end() || !pin_current(it->second)) return -1;
    name_current(role);
    return current_cpu() == it->second ? it->second : -1;
}

}  // namespace firm::affinity
