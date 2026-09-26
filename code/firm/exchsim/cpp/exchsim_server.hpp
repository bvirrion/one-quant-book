// firm.exchsim live server (One Quant Book 10, chapter 26), C++20, Linux sockets, single-threaded event loop.
//
//   order entry     TCP, SoupBinTCP 4.0 (login with username/password/session/sequence, heartbeats, sequenced
//                   replay on re-login), OUCH-style application messages (PROTOCOL.md section 2)
//   market data     MoldUDP64 packets on two lines A and B: UDP multicast on loopback (default) or UDP unicast
//                   to host:port pairs; a snapshot channel (own session and sequence); heartbeats
//   retransmission  TCP: a 20-byte MoldUDP64 request (session, seq, count) answered with u16-length-prefixed packets
//   drop copy       a read-only Soup session receiving every E and C of its firm
//   background      an engine journal (e.g. written by the Python simulator) replayed in real time; its sessions
//                   are renumbered from 10,000 so that they never meet live sessions
//   faults          scheduled: drop a session (close its socket), refuse logins over a window, pause the engine,
//                   halt an instrument (control P H ... P T)
//   input journal   every record the engine processed (t_ns, session, message), so that any run replays exactly
//                   through firm_exchsim_engine.Engine or exchsim_engine.hpp
//
// Time is nanoseconds since midnight (CLOCK_REALTIME), as in the feed. Configuration: a JSON object with the
// engine configuration under "engine" and the server's options (see ServerConfig::from_json).
#pragma once
#include "exchsim_engine.hpp"

#include <arpa/inet.h>
#include <fcntl.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <poll.h>
#include <sys/socket.h>
#include <unistd.h>

#include <atomic>
#include <chrono>
#include <cstdio>
#include <ctime>
#include <fstream>
#include <map>
#include <string>
#include <vector>

namespace firm::exchsim {

inline u64 now_ns() {
    timespec ts{};
    clock_gettime(CLOCK_REALTIME, &ts);
    return (static_cast<u64>(ts.tv_sec) % 86400ULL) * 1'000'000'000ULL + static_cast<u64>(ts.tv_nsec);
}

struct SessionConf {
    std::string username, password;
    u32 firm{};
    bool cod{true}, drop_copy{false};
};

struct FaultConf {
    std::string kind;            // drop_session | refuse_login | pause | halt
    double start_s{}, end_s{};   // seconds after the server starts
    std::string username;
    u16 locate{};
};

struct ServerConfig {
    json::Value engine;
    std::string bind = "127.0.0.1";
    int oe_port = 0, retrans_port = 0;           // 0: an ephemeral port (read it back with Server::port_*)
    bool multicast = true;
    std::string group = "239.192.10.1", snap_group = "239.192.10.2";
    int port_a = 0, port_b = 0, port_snap = 0;   // feed destinations (0 = no line)
    std::string dest_host = "127.0.0.1";         // unicast fallback destination
    u64 snapshot_every_ns = 0, heartbeat_ns = 1'000'000'000;
    std::size_t window = 100'000, max_retransmit = 1000;
    std::vector<SessionConf> sessions;
    std::string background;                      // an engine journal to replay in real time ("" = none)
    double speed = 1.0;
    bool open_now = true;                        // start messages, then continuous trading, at start
    std::string journal_out;                     // "" = keep the input journal in memory only
    std::vector<FaultConf> faults;

    static ServerConfig from_json(const json::Value& v) {
        ServerConfig c;
        c.engine = v["engine"];
        c.bind = v.get_str("bind", c.bind);
        c.oe_port = static_cast<int>(v.get_int("oe_port", 0));
        c.retrans_port = static_cast<int>(v.get_int("retrans_port", 0));
        c.multicast = !v.has("multicast") || v["multicast"].b;
        c.group = v.get_str("group", c.group);
        c.snap_group = v.get_str("snap_group", c.snap_group);
        c.port_a = static_cast<int>(v.get_int("port_a", 0));
        c.port_b = static_cast<int>(v.get_int("port_b", 0));
        c.port_snap = static_cast<int>(v.get_int("port_snap", 0));
        c.dest_host = v.get_str("dest_host", c.dest_host);
        c.snapshot_every_ns = static_cast<u64>(v.get_int("snapshot_every_ns", 0));
        c.heartbeat_ns = static_cast<u64>(v.get_int("heartbeat_ns", 1'000'000'000));
        c.background = v.get_str("background", "");
        c.open_now = !v.has("open_now") || v["open_now"].b;
        c.journal_out = v.get_str("journal_out", "");
        if (v.has("speed_permille")) c.speed = static_cast<double>(v["speed_permille"].i) / 1000.0;
        if (v.has("sessions"))
            for (const auto& s : v["sessions"].a)
                c.sessions.push_back({s["username"].s, s.get_str("password", ""), static_cast<u32>(s.get_int("firm", 1)),
                                      !s.has("cod") || s["cod"].b, s.has("drop_copy") && s["drop_copy"].b});
        if (v.has("faults"))
            for (const auto& f : v["faults"].a)
                c.faults.push_back({f["kind"].s, static_cast<double>(f.get_int("start_ms", 0)) / 1000.0,
                                    static_cast<double>(f.get_int("end_ms", 0)) / 1000.0, f.get_str("username", ""),
                                    static_cast<u16>(f.get_int("locate", 0))});
        return c;
    }
};

class Server {
public:
    explicit Server(ServerConfig cfg) : cfg_(std::move(cfg)), engine_(cfg_.engine) {
        session_name_ = cfg_.engine.get_str("session", cfg_.engine.get_str("venue", "SIMX"));
        session_name_.resize(10, ' ');
        snap_name_ = cfg_.engine.get_str("venue", "SIMX").substr(0, 9) + "S";
        snap_name_.resize(10, ' ');
        for (std::size_t i = 0; i < cfg_.sessions.size(); ++i) {
            Conn c;
            c.conf = cfg_.sessions[i];
            c.sid = static_cast<u16>(i + 1);
            conns_.push_back(std::move(c));
        }
    }
    ~Server() { close_all(); }

    // Binds every socket; after this the ports are known.
    void start() {
        start_wall_ = now_ns();
        oe_fd_ = listen_tcp(cfg_.oe_port);
        rt_fd_ = listen_tcp(cfg_.retrans_port);
        udp_fd_ = socket(AF_INET, SOCK_DGRAM, 0);
        if (cfg_.multicast) {
            in_addr lo{};
            inet_pton(AF_INET, "127.0.0.1", &lo);
            setsockopt(udp_fd_, IPPROTO_IP, IP_MULTICAST_IF, &lo, sizeof lo);
            const unsigned char loop = 1, ttl = 1;
            setsockopt(udp_fd_, IPPROTO_IP, IP_MULTICAST_LOOP, &loop, sizeof loop);
            setsockopt(udp_fd_, IPPROTO_IP, IP_MULTICAST_TTL, &ttl, sizeof ttl);
        }
        if (!cfg_.background.empty()) load_background();
        next_hb_ = start_wall_ + cfg_.heartbeat_ns;
        next_snap_ = cfg_.snapshot_every_ns ? start_wall_ + cfg_.snapshot_every_ns : 0;
        if (cfg_.open_now) {
            control_S('O');
            control_S('S');
            control_S('Q');
            Ctl p; p.type = 'P'; p.locate = 0; p.phase = 'T'; p.reason = {'O', 'P', 'E', 'N'};
            engine_input(0, ctl_bytes(p));
        }
    }

    // Runs the event loop until stop() is called (from another thread or a signal handler) or `for_ns` elapses.
    void run(u64 for_ns = 0) {
        const u64 until = for_ns ? now_ns() + for_ns : 0;
        while (!stop_.load()) {
            const u64 t = now_ns();
            if (until && t >= until) break;
            timers(t);
            poll_once(1);
        }
    }
    void stop() { stop_.store(true); }

    int port_oe() const { return bound_port(oe_fd_); }
    int port_retrans() const { return bound_port(rt_fd_); }
    const Bytes& journal() const { return journal_; }
    u64 feed_seq() const { return feed_seq_; }
    Engine& engine() { return engine_; }

private:
    struct Conn {
        SessionConf conf;
        u16 sid{};
        int fd{-1};
        Bytes in;
        std::vector<Bytes> sent;          // every sequenced frame for this session (numbered from 1)
        u64 last_rx{}, last_tx{};
        bool engine_logged{};
    };
    struct Pending { u64 due; u16 session; Bytes payload; };

    // -- sockets -----------------------------------------------------------------------------------------------
    int listen_tcp(int port) {
        int fd = socket(AF_INET, SOCK_STREAM, 0);
        const int one = 1;
        setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &one, sizeof one);
        sockaddr_in a{};
        a.sin_family = AF_INET;
        a.sin_port = htons(static_cast<u16>(port));
        inet_pton(AF_INET, cfg_.bind.c_str(), &a.sin_addr);
        if (bind(fd, reinterpret_cast<sockaddr*>(&a), sizeof a) != 0) throw std::runtime_error("bind failed");
        listen(fd, 16);
        fcntl(fd, F_SETFL, O_NONBLOCK);
        return fd;
    }
    static int bound_port(int fd) {
        sockaddr_in a{};
        socklen_t n = sizeof a;
        getsockname(fd, reinterpret_cast<sockaddr*>(&a), &n);
        return ntohs(a.sin_port);
    }
    void send_udp(const std::string& group, int port, const Bytes& pkt) {
        if (port <= 0) return;
        sockaddr_in d{};
        d.sin_family = AF_INET;
        d.sin_port = htons(static_cast<u16>(port));
        inet_pton(AF_INET, (cfg_.multicast ? group : cfg_.dest_host).c_str(), &d.sin_addr);
        sendto(udp_fd_, pkt.data(), pkt.size(), 0, reinterpret_cast<sockaddr*>(&d), sizeof d);
    }
    static void send_all(int fd, const Bytes& b) {
        std::size_t off = 0;
        while (off < b.size()) {
            const ssize_t n = ::send(fd, b.data() + off, b.size() - off, MSG_NOSIGNAL);
            if (n <= 0) return;
            off += static_cast<std::size_t>(n);
        }
    }
    void close_all() {
        for (auto& c : conns_) if (c.fd >= 0) { ::close(c.fd); c.fd = -1; }
        for (int fd : rt_clients_) ::close(fd);
        rt_clients_.clear();
        for (int* fd : {&oe_fd_, &rt_fd_, &udp_fd_}) if (*fd >= 0) { ::close(*fd); *fd = -1; }
    }

    // -- engine ------------------------------------------------------------------------------------------------
    static Bytes ctl_bytes(const Ctl& c) { Bytes b; encode(b, c); return b; }
    void control_S(char ev) { Ctl s; s.type = 'S'; s.event = ev; engine_input(0, ctl_bytes(s)); }
    void engine_input(u16 session, const Bytes& payload) {
        const u64 t = now_ns();
        journal_record(journal_, t, session, payload);
        if (!cfg_.journal_out.empty()) {
            std::ofstream f(cfg_.journal_out, std::ios::binary | std::ios::app);
            Bytes one;
            journal_record(one, t, session, payload);
            f.write(reinterpret_cast<const char*>(one.data()), static_cast<std::streamsize>(one.size()));
        }
        engine_.process(t, session, payload);
        publish();
    }
    void publish() {
        if (!engine_.feed.empty()) {
            std::vector<Bytes> chunk;
            std::size_t size = 0;
            u64 first = feed_seq_ + 1;
            for (const auto& m : engine_.feed) {
                Bytes b;
                encode(b, m);
                window_.push_back(b);
                if (window_.size() > cfg_.window) window_.pop_front();
                ++feed_seq_;
                if (!chunk.empty() && size + 2 + b.size() > 1400 - 20) {
                    send_packet(mold_packet(session_name_, first, chunk));
                    first += chunk.size();
                    chunk.clear();
                    size = 0;
                }
                size += 2 + b.size();
                chunk.push_back(std::move(b));
            }
            if (!chunk.empty()) send_packet(mold_packet(session_name_, first, chunk));
        }
        for (const auto& [sid, m] : engine_.reports) {
            Bytes app;
            encode(app, m);
            const Bytes frame = soup_frame('S', app);
            if (Conn* c = by_sid(sid)) deliver(*c, frame);
            if (m.type == 'E' || m.type == 'C') {
                if (Conn* c = by_sid(sid)) {
                    for (auto& dc : conns_)
                        if (dc.conf.drop_copy && dc.conf.firm == c->conf.firm) deliver(dc, frame);
                }
            }
        }
    }
    void send_packet(const Bytes& pkt) {
        send_udp(cfg_.group, cfg_.port_a, pkt);
        send_udp(cfg_.group, cfg_.port_b, pkt);
        last_feed_ = now_ns();
    }
    void deliver(Conn& c, const Bytes& frame) {
        c.sent.push_back(frame);
        if (c.fd >= 0) { send_all(c.fd, frame); c.last_tx = now_ns(); }
    }
    Conn* by_sid(u16 sid) {
        for (auto& c : conns_) if (c.sid == sid) return &c;
        return nullptr;
    }

    // -- background journal --------------------------------------------------------------------------------------
    void load_background() {
        std::ifstream in(cfg_.background, std::ios::binary);
        const Bytes data((std::istreambuf_iterator<char>(in)), std::istreambuf_iterator<char>());
        u64 t0 = 0;
        bool first = true;
        for_each_record(data, [&](const JournalRecord& r) {
            if (first) { t0 = r.t_ns; first = false; }
            Bytes p(r.payload.begin(), r.payload.end());
            u16 s = r.session;
            if (s == 0) {
                Ctl c = decode_ctl(r.payload);
                if (c.type == 'L' || c.type == 'D') { c.session = static_cast<u16>(c.session + 10000); p = ctl_bytes(c); }
            } else {
                s = static_cast<u16>(s + 10000);
            }
            const u64 due = start_wall_ + static_cast<u64>(static_cast<double>(r.t_ns - t0) / cfg_.speed);
            background_.push_back({due, s, std::move(p)});
        });
    }

    // -- timers ------------------------------------------------------------------------------------------------
    bool paused(u64 t) const {
        for (const auto& f : cfg_.faults)
            if (f.kind == "pause" && t >= start_wall_ + static_cast<u64>(f.start_s * 1e9) &&
                t < start_wall_ + static_cast<u64>(f.end_s * 1e9))
                return true;
        return false;
    }
    void timers(u64 t) {
        if (!paused(t)) {
            while (bg_i_ < background_.size() && background_[bg_i_].due <= t) {
                const auto& r = background_[bg_i_++];
                engine_input(r.session, r.payload);
            }
            for (auto& p : queued_) engine_input(p.session, p.payload);
            queued_.clear();
        }
        for (std::size_t k = 0; k < cfg_.faults.size(); ++k) {
            const auto& f = cfg_.faults[k];
            const u64 a = start_wall_ + static_cast<u64>(f.start_s * 1e9);
            const u64 b = start_wall_ + static_cast<u64>(f.end_s * 1e9);
            if (fired_.size() < cfg_.faults.size()) fired_.resize(cfg_.faults.size(), 0);
            if (f.kind == "drop_session" && t >= a && !(fired_[k] & 1)) {
                fired_[k] |= 1;
                for (auto& c : conns_) if (c.conf.username == f.username) disconnect(c);
            }
            if (f.kind == "halt") {
                if (t >= a && !(fired_[k] & 1)) {
                    fired_[k] |= 1;
                    Ctl p; p.type = 'P'; p.locate = f.locate; p.phase = 'H'; p.reason = {'H', 'A', 'L', 'T'};
                    engine_input(0, ctl_bytes(p));
                }
                if (t >= b && !(fired_[k] & 2)) {
                    fired_[k] |= 2;
                    Ctl p; p.type = 'P'; p.locate = f.locate; p.phase = 'T'; p.reason = {'R', 'E', 'S', 'M'};
                    engine_input(0, ctl_bytes(p));
                }
            }
        }
        if (t >= next_hb_) {
            next_hb_ = t + cfg_.heartbeat_ns;
            if (t - last_feed_ >= cfg_.heartbeat_ns) {
                const Bytes hb = mold_packet(session_name_, feed_seq_ + 1, {});
                send_udp(cfg_.group, cfg_.port_a, hb);
                send_udp(cfg_.group, cfg_.port_b, hb);
            }
            for (auto& c : conns_) {
                if (c.fd < 0) continue;
                if (t - c.last_rx > 15 * cfg_.heartbeat_ns) { disconnect(c); continue; }
                const Bytes h = soup_frame('H');
                send_all(c.fd, h);
            }
        }
        if (next_snap_ && t >= next_snap_) {
            next_snap_ = t + cfg_.snapshot_every_ns;
            for (u16 loc : engine_.locates()) {
                const auto snap = engine_.snapshot(loc, feed_seq_, t);
                std::vector<Bytes> chunk;
                std::size_t size = 0;
                for (const auto& m : snap) {
                    Bytes b; encode(b, m);
                    if (!chunk.empty() && size + 2 + b.size() > 1400 - 20) {
                        send_udp(cfg_.snap_group, cfg_.port_snap, mold_packet(snap_name_, snap_seq_, chunk));
                        snap_seq_ += chunk.size(); chunk.clear(); size = 0;
                    }
                    size += 2 + b.size();
                    chunk.push_back(std::move(b));
                }
                if (!chunk.empty()) {
                    send_udp(cfg_.snap_group, cfg_.port_snap, mold_packet(snap_name_, snap_seq_, chunk));
                    snap_seq_ += chunk.size();
                }
            }
        }
    }
    bool refusing(u64 t) const {
        for (const auto& f : cfg_.faults)
            if (f.kind == "refuse_login" && t >= start_wall_ + static_cast<u64>(f.start_s * 1e9) &&
                t < start_wall_ + static_cast<u64>(f.end_s * 1e9))
                return true;
        return false;
    }

    // -- the poll loop -------------------------------------------------------------------------------------------
    void poll_once(int timeout_ms) {
        std::vector<pollfd> fds;
        fds.push_back({oe_fd_, POLLIN, 0});
        fds.push_back({rt_fd_, POLLIN, 0});
        for (auto& c : conns_) if (c.fd >= 0) fds.push_back({c.fd, POLLIN, 0});
        for (int fd : rt_clients_) fds.push_back({fd, POLLIN, 0});
        if (::poll(fds.data(), fds.size(), timeout_ms) <= 0) return;
        if (fds[0].revents & POLLIN) accept_oe();
        if (fds[1].revents & POLLIN) {
            const int fd = ::accept(rt_fd_, nullptr, nullptr);
            if (fd >= 0) rt_clients_.push_back(fd);
        }
        for (std::size_t i = 2; i < fds.size(); ++i) {
            if (!(fds[i].revents & (POLLIN | POLLHUP | POLLERR))) continue;
            bool is_rt = false;
            for (int fd : rt_clients_) is_rt = is_rt || fd == fds[i].fd;
            if (is_rt) serve_retransmit(fds[i].fd);
            else for (auto& c : conns_) if (c.fd == fds[i].fd) read_conn(c);
        }
    }
    void accept_oe() {
        const int fd = ::accept(oe_fd_, nullptr, nullptr);
        if (fd < 0) return;
        const int one = 1;
        setsockopt(fd, IPPROTO_TCP, TCP_NODELAY, &one, sizeof one);
        // The login request is read synchronously (it is the first frame the client sends).
        Bytes buf(49);
        std::size_t got = 0;
        while (got < 49) {
            const ssize_t n = ::recv(fd, buf.data() + got, 49 - got, 0);
            if (n <= 0) { ::close(fd); return; }
            got += static_cast<std::size_t>(n);
        }
        if (buf[2] != 'L') { ::close(fd); return; }
        const Span s(buf.data() + 3, 46);
        const std::string user = get_alpha(s, 0, 6), pass = get_alpha(s, 6, 10), sess = get_alpha(s, 16, 10);
        const std::string seqs = get_alpha(s, 26, 20);
        u64 want = 0;
        for (char ch : seqs) if (ch >= '0' && ch <= '9') want = want * 10 + static_cast<u64>(ch - '0');
        Conn* c = nullptr;
        for (auto& x : conns_) if (x.conf.username == user && x.conf.password == pass) c = &x;
        std::string trimmed = session_name_;
        while (!trimmed.empty() && trimmed.back() == ' ') trimmed.pop_back();
        char reject = 0;
        if (c == nullptr) reject = 'A';
        else if (refusing(now_ns()) || c->fd >= 0 || (!sess.empty() && sess != trimmed)) reject = 'S';
        if (reject) {
            const u8 r = static_cast<u8>(reject);
            send_all(fd, soup_frame('J', Span(&r, 1)));
            ::close(fd);
            return;
        }
        fcntl(fd, F_SETFL, O_NONBLOCK);
        c->fd = fd;
        c->in.clear();
        c->last_rx = now_ns();
        const u64 next = c->sent.size() + 1;
        const u64 from = want == 0 ? next : want;
        Bytes acc;
        put_alpha(acc, session_name_, 10);
        put_alpha(acc, num20(from), 20);
        send_all(fd, soup_frame('A', acc));
        for (u64 k = from; k < next; ++k) send_all(fd, c->sent[k - 1]);
        if (!c->engine_logged && !c->conf.drop_copy) {
            Ctl l; l.type = 'L'; l.session = c->sid; l.firm = c->conf.firm; l.cod = c->conf.cod ? 'Y' : 'N';
            engine_input(0, ctl_bytes(l));
            c->engine_logged = true;
        }
    }
    void disconnect(Conn& c) {
        if (c.fd >= 0) { ::close(c.fd); c.fd = -1; }
        if (c.engine_logged) {
            Ctl d; d.type = 'D'; d.session = c.sid;
            engine_input(0, ctl_bytes(d));
            c.engine_logged = false;
        }
    }
    void read_conn(Conn& c) {
        u8 buf[65536];
        const ssize_t n = ::recv(c.fd, buf, sizeof buf, 0);
        if (n <= 0) { disconnect(c); return; }
        c.in.insert(c.in.end(), buf, buf + n);
        c.last_rx = now_ns();
        std::size_t i = 0;
        while (i + 2 <= c.in.size()) {
            const std::size_t len = static_cast<std::size_t>(get(c.in, i, 2));
            if (i + 2 + len > c.in.size()) break;
            const char type = static_cast<char>(c.in[i + 2]);
            if (type == 'U' && !c.conf.drop_copy) {
                Bytes app(c.in.begin() + static_cast<long>(i + 3), c.in.begin() + static_cast<long>(i + 2 + len));
                if (paused(now_ns())) queued_.push_back({0, c.sid, std::move(app)});
                else engine_input(c.sid, app);
            } else if (type == 'O') {
                send_all(c.fd, soup_frame('Z'));
                disconnect(c);
                return;
            }
            i += 2 + len;
        }
        c.in.erase(c.in.begin(), c.in.begin() + static_cast<long>(i));
    }
    void serve_retransmit(int fd) {
        u8 req[20];
        const ssize_t n = ::recv(fd, req, sizeof req, MSG_WAITALL);
        if (n != 20) {
            ::close(fd);
            rt_clients_.erase(std::find(rt_clients_.begin(), rt_clients_.end(), fd));
            return;
        }
        const Span s(req, 20);
        const u64 seq = get(s, 10, 8);
        u64 count = get(s, 18, 2);
        const u64 lo = feed_seq_ >= window_.size() ? feed_seq_ - window_.size() + 1 : 1;
        if (seq < lo || seq > feed_seq_) {
            Bytes empty = mold_packet(session_name_, seq, {});
            Bytes out; put(out, empty.size(), 2); out.insert(out.end(), empty.begin(), empty.end());
            send_all(fd, out);
            return;
        }
        count = std::min<u64>({count, cfg_.max_retransmit, feed_seq_ - seq + 1});
        std::vector<Bytes> chunk;
        std::size_t size = 0;
        u64 first = seq;
        Bytes out;
        for (u64 k = seq; k < seq + count; ++k) {
            const Bytes& m = window_[k - lo];
            if (!chunk.empty() && size + 2 + m.size() > 1400 - 20) {
                const Bytes p = mold_packet(session_name_, first, chunk);
                put(out, p.size(), 2); out.insert(out.end(), p.begin(), p.end());
                first += chunk.size(); chunk.clear(); size = 0;
            }
            size += 2 + m.size();
            chunk.push_back(m);
        }
        if (!chunk.empty()) {
            const Bytes p = mold_packet(session_name_, first, chunk);
            put(out, p.size(), 2); out.insert(out.end(), p.begin(), p.end());
        }
        send_all(fd, out);
    }

    ServerConfig cfg_;
    Engine engine_;
    std::string session_name_, snap_name_;
    std::vector<Conn> conns_;
    std::vector<int> rt_clients_;
    int oe_fd_{-1}, rt_fd_{-1}, udp_fd_{-1};
    u64 start_wall_{}, next_hb_{}, next_snap_{}, last_feed_{}, feed_seq_{}, snap_seq_{1};
    std::deque<Bytes> window_;
    Bytes journal_;
    std::vector<Pending> background_, queued_;
    std::size_t bg_i_{};
    std::vector<int> fired_;
    std::atomic<bool> stop_{false};
};

}  // namespace firm::exchsim
