// firm.ticktotrade (C++20): the live harness. Four threads on the loopback interface:
//   exchange  sends the recorded line's packets over UDP, on line A and 5 us later on line B, at a stretched pace
//   feed      receives both lines, runs the feed handler, publishes each event on a single-producer ring
//   engine    takes events off the ring and runs the Path: book, strategy, risk gate, gateway, send over TCP
//   venue     receives the order-entry session's frames and time-stamps each order
// Every stage stamps the time-stamp counter; run_live() returns the stamps of every order, the orders themselves (to
// compare with the offline replay) and the allocation count after warm-up.
#pragma once
#include <arpa/inet.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <pthread.h>
#include <sched.h>
#include <sys/socket.h>
#include <unistd.h>

#include <atomic>
#include <cstdint>
#include <stdexcept>
#include <thread>
#include <vector>

#include "../../arena/cpp/firm_alloc_count.hpp"
#include "../../feedhandler/cpp/firm_feedhandler.hpp"
#include "../../ring/cpp/firm_ring.hpp"
#include "../../ubench/cpp/firm_ubench.hpp"
#include "firm_ticktotrade.hpp"

namespace firm::t2t {

struct Config {
    std::vector<std::uint8_t> line;      // the recorded line
    std::uint32_t tick = 1;
    double stretch = 20.0;               // recorded time is multiplied by this when replayed
    std::uint64_t b_delay_ns = 5'000;    // line B follows line A
    int cpu_exchange = -1, cpu_feed = -1, cpu_engine = -1, cpu_venue = -1;
    std::size_t warmup_events = 200;     // allocations are counted after this many events
};

struct OrderStamp {
    Stamp s;
    std::uint64_t exch = 0, venue = 0;  // packet sent by the exchange, order received by the venue (TSC)
    int nth = 0;                        // the order's rank among those of its event (0: the first)
};

struct Result {
    std::vector<OrderStamp> orders;
    std::vector<OrderOut> out;
    std::uint64_t events = 0, packets_a = 0, packets_b = 0, duplicates = 0;
    long long allocations_after_warmup = -1;
    double ticks_per_ns = 1.0;
};

namespace detail {

inline void pin(int cpu) {
    if (cpu < 0) return;
    cpu_set_t s;
    CPU_ZERO(&s);
    CPU_SET(cpu, &s);
    pthread_setaffinity_np(pthread_self(), sizeof s, &s);
}

inline std::uint64_t tsc() { return ubench::rdtscp(); }

inline int udp_bound(std::uint16_t& port) {
    const int fd = ::socket(AF_INET, SOCK_DGRAM, 0);
    int big = 4 << 20;
    ::setsockopt(fd, SOL_SOCKET, SO_RCVBUF, &big, sizeof big);
    sockaddr_in a{};
    a.sin_family = AF_INET;
    a.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    a.sin_port = 0;
    if (::bind(fd, reinterpret_cast<sockaddr*>(&a), sizeof a) != 0) throw std::runtime_error("bind udp");
    socklen_t n = sizeof a;
    ::getsockname(fd, reinterpret_cast<sockaddr*>(&a), &n);
    port = ntohs(a.sin_port);
    return fd;
}

// A ring message: the event, where it came from, and the stamps taken so far.
struct Msg {
    strat::Event e;
    std::uint64_t pkt_seq, recv, pub;
    char line;
};

}  // namespace detail

inline Result run_live(const Config& cfg) {
    using namespace detail;
    Result res;
    const ubench::Clock clk = ubench::Clock::calibrate(20);
    res.ticks_per_ns = clk.ticks_per_ns;
    const auto packets = feed2::recorded(cfg.line);

    // sockets: two UDP lines into the feed thread, one TCP session from the engine to the venue
    std::uint16_t port_a = 0, port_b = 0;
    const int rx_a = udp_bound(port_a), rx_b = udp_bound(port_b);
    const int tx = ::socket(AF_INET, SOCK_DGRAM, 0);
    const int lst = ::socket(AF_INET, SOCK_STREAM, 0);
    sockaddr_in va{};
    va.sin_family = AF_INET;
    va.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    ::bind(lst, reinterpret_cast<sockaddr*>(&va), sizeof va);
    ::listen(lst, 1);
    socklen_t vn = sizeof va;
    ::getsockname(lst, reinterpret_cast<sockaddr*>(&va), &vn);
    const int cli = ::socket(AF_INET, SOCK_STREAM, 0);
    int one = 1;
    ::setsockopt(cli, IPPROTO_TCP, TCP_NODELAY, &one, sizeof one);
    if (::connect(cli, reinterpret_cast<sockaddr*>(&va), sizeof va) != 0) throw std::runtime_error("connect");
    const int srv = ::accept(lst, nullptr, nullptr);

    // preallocated state: stamps, the exchange's send times per (line, packet), the venue's receive times per order
    std::vector<std::uint64_t> sent_a(packets.size()), sent_b(packets.size());
    std::vector<std::uint64_t> first_seq(packets.size());
    for (std::size_t i = 0; i < packets.size(); ++i) first_seq[i] = feed2::be64(packets[i].p + 10);
    res.orders.reserve(1 << 16);
    std::vector<std::pair<std::uint64_t, std::uint64_t>> venue_rx;  // (cl, tsc)
    venue_rx.reserve(1 << 16);
    std::vector<std::uint8_t> arena(cfg.line.size() * 2 + 4096);     // received packets stay where the handler saw them
    std::vector<std::uint8_t> ring_mem(ring::region_size(1 << 14, 128));
    ring::format(ring_mem.data(), 1 << 14, 128);
    ring::Spsc ring_out(ring_mem.data()), ring_in(ring_mem.data());  // the producer's and the consumer's handles
    std::atomic<bool> feed_done{false}, engine_done{false}, stop_venue{false}, exch_done{false};
    std::atomic<int> ready{0};
    std::atomic<long long> alloc_mark{-1}, alloc_end{-1};

    std::thread venue([&] {
        pin(cfg.cpu_venue);
        ++ready;
        std::uint8_t buf[1 << 16];
        std::size_t have = 0;
        while (!stop_venue.load(std::memory_order_acquire)) {
            const ssize_t r = ::recv(srv, buf + have, sizeof buf - have, MSG_DONTWAIT);
            if (r <= 0) continue;
            const std::uint64_t now = tsc();
            have += static_cast<std::size_t>(r);
            std::size_t p = 0;
            while (have - p >= 3) {  // SoupBinTCP frames: u16 length | type | payload
                const std::size_t n = (std::size_t(buf[p]) << 8) | buf[p + 1];
                if (have - p < 2 + n) break;
                if (buf[p + 2] == 'U') {  // unsequenced data: an order message; a replace is known by its new id
                    const std::uint8_t* m = buf + p + 3;
                    venue_rx.emplace_back(wire::be64(m + (m[0] == 'U' ? 9 : 1)), now);
                }
                p += 2 + n;
            }
            std::memmove(buf, buf + p, have - p);
            have -= p;
        }
    });

    std::thread engine([&] {
        pin(cfg.cpu_engine);
        Path path(cfg.tick);  // built (and its memory touched) before the exchange starts
        ++ready;
        detail::Msg m;
        std::uint8_t frame[80];
        std::uint64_t n_ev = 0;
        for (;;) {
            if (ring_in.try_read(&m, sizeof m) < 0) {
                if (feed_done.load(std::memory_order_acquire) && ring_in.try_read(&m, sizeof m) < 0)
                    break;
                continue;
            }
            if (n_ev++ == cfg.warmup_events)
                alloc_mark.store(static_cast<long long>(firm::arena::allocations()));
            Stamp st;
            st.t[Recv] = m.recv, st.t[Pub] = m.pub, st.t[Pop] = tsc();
            st.pkt_seq = m.pkt_seq, st.line = m.line;
            int nth = 0;
            auto send = [&](const std::uint8_t* msg, std::size_t n, char, std::uint64_t) {
                frame[0] = static_cast<std::uint8_t>((n + 1) >> 8);  // SoupBinTCP: length, 'U', message
                frame[1] = static_cast<std::uint8_t>(n + 1);
                frame[2] = 'U';
                std::memcpy(frame + 3, msg, n);
                ::send(cli, frame, n + 3, 0);
                OrderStamp os;
                os.s = st;
                os.s.t[Sent] = tsc();
                os.nth = nth++;  // a second order of the same event has waited for the first one's send
                res.orders.push_back(os);
            };
            path.on_event(m.e, &tsc, &st, send);
        }
        alloc_end.store(static_cast<long long>(firm::arena::allocations()));  // before the copy below
        res.out = path.out;
        engine_done.store(true, std::memory_order_release);
    });

    std::thread feed([&] {
        pin(cfg.cpu_feed);
        ++ready;
        feed2::Handler h;
        std::uint64_t cur_seq = 0, recv = 0;
        char cur_line = 0;
        h.on_event = [&](const feed2::Event& e) {
            detail::Msg m{e, cur_seq, recv, tsc(), cur_line};
            while (!ring_out.try_write(&m, sizeof m)) {
            }
        };
        std::size_t used = 0, got_a = 0, got_b = 0;
        const std::uint64_t t0_rec = packets.empty() ? 0 : packets[0].t, t0 = tsc();
        const auto idle = static_cast<std::uint64_t>(50e6 * clk.ticks_per_ns);
        std::uint64_t last = t0;
        while (got_a < packets.size() || got_b < packets.size()) {
            if (exch_done.load(std::memory_order_acquire) && tsc() - last > idle) break;  // a packet lost on both
            for (int s = 0; s < 2; ++s) {
                const int fd = s ? rx_b : rx_a;
                const ssize_t r = ::recv(fd, arena.data() + used, 2048, MSG_DONTWAIT);
                if (r <= 0) continue;
                recv = last = tsc();
                const std::uint8_t* p = arena.data() + used;
                used += static_cast<std::size_t>(r);
                cur_seq = feed2::be64(p + 10), cur_line = s ? 'B' : 'A';
                (s ? got_b : got_a)++;
                // the handler's clock is the recording's: arrival mapped back through the stretch
                const auto t_rec = t0_rec + static_cast<std::uint64_t>(clk.ns(recv - t0) / cfg.stretch);
                h.on_packet(t_rec, cur_line, p);
            }
        }
        res.events = h.events;
        res.packets_a = got_a, res.packets_b = got_b, res.duplicates = h.c.duplicates;
        feed_done.store(true, std::memory_order_release);
    });

    while (ready.load() < 3) {
    }
    pin(cfg.cpu_exchange);
    {  // the exchange: this thread
        sockaddr_in da{};
        da.sin_family = AF_INET;
        da.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
        const std::uint64_t start = tsc() + static_cast<std::uint64_t>(1e6 * clk.ticks_per_ns);  // 1 ms from now
        const std::uint64_t b_ticks = static_cast<std::uint64_t>(cfg.b_delay_ns * clk.ticks_per_ns);
        for (std::size_t i = 0; i < packets.size(); ++i) {
            const std::uint64_t due = start + static_cast<std::uint64_t>(
                                                  (packets[i].t - packets[0].t) * cfg.stretch * clk.ticks_per_ns);
            while (tsc() < due) {
            }
            da.sin_port = htons(port_a);
            sent_a[i] = tsc();
            ::sendto(tx, packets[i].p, packets[i].n, 0, reinterpret_cast<sockaddr*>(&da), sizeof da);
            while (tsc() < sent_a[i] + b_ticks) {
            }
            da.sin_port = htons(port_b);
            sent_b[i] = tsc();
            ::sendto(tx, packets[i].p, packets[i].n, 0, reinterpret_cast<sockaddr*>(&da), sizeof da);
        }
        exch_done.store(true, std::memory_order_release);
    }
    feed.join();
    engine.join();
    const std::uint64_t settle = tsc() + static_cast<std::uint64_t>(20e6 * clk.ticks_per_ns);  // 20 ms for the venue
    while (tsc() < settle) {
    }
    stop_venue.store(true, std::memory_order_release);
    venue.join();
    const long long mark = alloc_mark.load();
    res.allocations_after_warmup = mark < 0 ? -1 : alloc_end.load() - mark;

    // join the other threads' stamps: the exchange's send of the packet, the venue's receipt of the order
    std::map<std::uint64_t, std::size_t> by_seq;
    for (std::size_t i = 0; i < packets.size(); ++i) by_seq[first_seq[i]] = i;
    std::map<std::uint64_t, std::uint64_t> venue_at;
    for (const auto& [cl, t] : venue_rx) venue_at.emplace(cl, t);
    for (auto& o : res.orders) {
        auto it = by_seq.upper_bound(o.s.pkt_seq);  // the packet whose first sequence number is at or before it
        if (it != by_seq.begin()) --it;
        o.exch = o.s.line == 'B' ? sent_b[it->second] : sent_a[it->second];
        auto v = venue_at.find(o.s.cl);
        o.venue = v == venue_at.end() ? 0 : v->second;
    }
    for (int fd : {rx_a, rx_b, tx, lst, cli, srv}) ::close(fd);
    return res;
}

}  // namespace firm::t2t
