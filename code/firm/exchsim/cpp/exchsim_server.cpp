// firm.exchsim live server: exchsim_server --config cfg.json [--seconds N]
// Prints its ports, runs until SIGINT/SIGTERM (or N seconds), and writes the input journal if configured.
#include "exchsim_server.hpp"

#include <csignal>
#include <cstdio>
#include <fstream>
#include <sstream>

static firm::exchsim::Server* g_server = nullptr;
static void on_signal(int) { if (g_server) g_server->stop(); }

int main(int argc, char** argv) {
    std::string path;
    double seconds = 0;
    for (int i = 1; i + 1 < argc; ++i) {
        const std::string a = argv[i];
        if (a == "--config") path = argv[++i];
        else if (a == "--seconds") seconds = std::stod(argv[++i]);
    }
    if (path.empty()) { std::fprintf(stderr, "usage: exchsim_server --config cfg.json [--seconds N]\n"); return 2; }
    std::ifstream f(path);
    std::stringstream ss;
    ss << f.rdbuf();
    const std::string text = ss.str();
    firm::exchsim::Server srv(firm::exchsim::ServerConfig::from_json(firm::exchsim::json::parse(text)));
    srv.start();
    g_server = &srv;
    std::signal(SIGINT, on_signal);
    std::signal(SIGTERM, on_signal);
    std::printf("exchsim_server: order entry tcp/%d, retransmission tcp/%d\n", srv.port_oe(), srv.port_retrans());
    std::fflush(stdout);
    srv.run(seconds > 0 ? static_cast<std::uint64_t>(seconds * 1e9) : 0);
    std::printf("exchsim_server: %llu feed messages, %zu journal bytes\n",
                static_cast<unsigned long long>(srv.feed_seq()), srv.journal().size());
    return 0;
}
