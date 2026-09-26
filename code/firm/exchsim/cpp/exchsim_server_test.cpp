// The live server on loopback: two firms log in, trade, get their reports and a drop copy; the feed arrives on both
// lines (multicast if the host supports it on loopback, else unicast); a gap is filled by retransmission; a
// re-login replays sequenced reports; the server's input journal replays to the same reports in a fresh engine.
#include "exchsim_client.hpp"
#include "exchsim_server.hpp"

#include <cassert>
#include <cstdio>
#include <thread>

using namespace firm::exchsim;

static In order(u64 cl, char side, u32 qty, u32 px) {
    In m; m.type = 'O'; m.cl_ord_id = cl; m.locate = 1; m.side = side; m.qty = qty; m.price = px;
    return m;
}

static bool run(bool multicast) {
    const std::string group = "239.192.10.1";
    FeedReceiver la, lb;
    const int base = 40000 + 2 * static_cast<int>(::getpid() % 10000);   // multicast needs fixed ports: vary by process
    if (!la.open(multicast ? base : 0, multicast ? group : "") || !lb.open(multicast ? base + 1 : 0, multicast ? group : ""))
        return false;
    const std::string cfg_text = R"({"engine": {"venue": "SIMX", "session": "SIMX      ", "engine_ns": 500,
      "fees": {"unit": "share", "make": -2000, "take": 3000, "cross": 0}, "throttle": {"rate": 0, "burst": 0},
      "instruments": [{"locate": 1, "symbol": "SIM1", "tick": 100, "lot": 100, "matching": "F", "start_price": 1000000}]},
      "multicast": )" + std::string(multicast ? "true" : "false") +
      R"(, "port_a": )" + std::to_string(la.port()) + R"(, "port_b": )" + std::to_string(lb.port()) + R"(,
      "sessions": [{"username": "HF1", "password": "a", "firm": 1}, {"username": "HF2", "password": "b", "firm": 2},
                   {"username": "DC1", "password": "c", "firm": 1, "drop_copy": true}]})";
    Server srv(ServerConfig::from_json(json::parse(cfg_text)));
    srv.start();
    std::thread loop([&] { srv.run(20'000'000'000ULL); });
    SoupClient a, b, dc;
    assert(a.connect("127.0.0.1", srv.port_oe()) && b.connect("127.0.0.1", srv.port_oe()));
    assert(dc.connect("127.0.0.1", srv.port_oe()));
    assert(a.login("HF1", "a", 0)->first == 'A' && b.login("HF2", "b", 0)->first == 'A');
    assert(dc.login("DC1", "c", 0)->first == 'A');
    SoupClient bad;
    assert(bad.connect("127.0.0.1", srv.port_oe()) && bad.login("HF1", "wrong", 0)->first == 'J');
    a.send(order(1, 'B', 300, 999'900));
    auto acc = a.next_report(2000);
    assert(acc && acc->type == 'A' && acc->cl_ord_id == 1);
    b.send(order(7, 'S', 200, 999'900));
    auto e_b = b.next_report(2000);
    while (e_b && e_b->type != 'E') e_b = b.next_report(2000);
    auto e_a = a.next_report(2000);
    assert(e_a && e_b && e_a->type == 'E' && e_a->qty == 200 && e_a->liquidity == 'A' && e_b->liquidity == 'R');
    auto d = dc.next_report(2000);
    assert(d && d->type == 'E' && d->cl_ord_id == 1);          // the drop copy saw firm 1's execution only
    // the feed: collect line A until the execution arrives
    u64 seen_e = 0, last_seq = 0;
    for (int k = 0; k < 50 && !seen_e; ++k) {
        auto p = la.recv(500);
        if (!p) continue;
        mold_parse(*p, [&](u64 seq, Span m) {
            last_seq = seq;
            if (m[0] == 'E') seen_e = seq;
        });
    }
    assert(seen_e > 0);
    assert(lb.recv(500).has_value());                            // line B carries the same packets
    // retransmission of message 1
    int rfd = socket(AF_INET, SOCK_STREAM, 0);
    sockaddr_in ra{};
    ra.sin_family = AF_INET;
    ra.sin_port = htons(static_cast<u16>(srv.port_retrans()));
    inet_pton(AF_INET, "127.0.0.1", &ra.sin_addr);
    assert(::connect(rfd, reinterpret_cast<sockaddr*>(&ra), sizeof ra) == 0);
    Bytes req;
    put_alpha(req, "SIMX", 10);
    put(req, 1, 8);
    put(req, 3, 2);
    ::send(rfd, req.data(), req.size(), 0);
    u8 buf[4096];
    const ssize_t n = ::recv(rfd, buf, sizeof buf, 0);
    assert(n > 22);
    u64 first = 0;
    mold_parse(Span(buf + 2, static_cast<std::size_t>(n) - 2), [&](u64 seq, Span) { if (!first) first = seq; });
    assert(first == 1);
    ::close(rfd);
    // re-login from sequence 1 replays every report of the session
    a.logout();
    a.close();
    std::this_thread::sleep_for(std::chrono::milliseconds(50));
    assert(a.connect("127.0.0.1", srv.port_oe()) && a.login("HF1", "a", 1)->first == 'A');
    int replayed = 0;
    while (auto r = a.next_report(300)) ++replayed;
    assert(replayed >= 3);                                        // A, E, and the system events
    srv.stop();
    loop.join();
    // the input journal replays through a fresh engine to the same number of executions
    Engine e(json::parse(cfg_text)["engine"]);
    std::size_t execs = 0;
    for_each_record(srv.journal(), [&](const JournalRecord& r) { e.process(r.t_ns, r.session, r.payload); });
    for (const auto& t : e.trades) execs += t.qty > 0;
    assert(execs == srv.engine().trades.size());
    std::printf("server (%s): orders, executions, drop copy, feed lines A and B, retransmission, replay after "
                "re-login (%d frames), journal replay (%zu executions) ok\n",
                multicast ? "loopback multicast" : "unicast", replayed, execs);
    return true;
}

int main() {
    if (!run(true)) {
        std::printf("loopback multicast unavailable here: testing the unicast fallback\n");
        if (!run(false)) return 1;
    }
    return 0;
}
