// firm.exchsim minimal test client (One Quant Book 10, chapter 26), C++20: a blocking SoupBinTCP session and a UDP
// feed receiver, enough to test the server. The real clients (feed handler, book builder, order gateway) are
// One Quant Book 13's.
#pragma once
#include "exchsim_codec.hpp"

#include <arpa/inet.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <poll.h>
#include <sys/socket.h>
#include <unistd.h>

#include <optional>
#include <string>
#include <utility>

namespace firm::exchsim {

class SoupClient {
public:
    ~SoupClient() { close(); }
    bool connect(const std::string& host, int port) {
        fd_ = socket(AF_INET, SOCK_STREAM, 0);
        sockaddr_in a{};
        a.sin_family = AF_INET;
        a.sin_port = htons(static_cast<u16>(port));
        inet_pton(AF_INET, host.c_str(), &a.sin_addr);
        const int one = 1;
        setsockopt(fd_, IPPROTO_TCP, TCP_NODELAY, &one, sizeof one);
        return ::connect(fd_, reinterpret_cast<sockaddr*>(&a), sizeof a) == 0;
    }
    // Sends the login request; returns the server's answer ('A' accepted with its payload, or 'J').
    std::optional<std::pair<char, Bytes>> login(const std::string& user, const std::string& pass, u64 seq,
                                                const std::string& session = "") {
        Bytes p;
        put_alpha(p, user, 6);
        put_alpha(p, pass, 10);
        put_alpha(p, session, 10);
        put_alpha(p, num20(seq), 20);
        raw(soup_frame('L', p));
        return recv(2000);
    }
    void send(const In& m) {
        Bytes app;
        encode(app, m);
        raw(soup_frame('U', app));
    }
    void heartbeat() { raw(soup_frame('R')); }
    void logout() { raw(soup_frame('O')); }
    // Next whole frame (type, payload) within timeout_ms, or nothing.
    std::optional<std::pair<char, Bytes>> recv(int timeout_ms) {
        while (true) {
            if (buf_.size() >= 2) {
                const std::size_t n = static_cast<std::size_t>(get(buf_, 0, 2));
                if (buf_.size() >= 2 + n) {
                    std::pair<char, Bytes> f{static_cast<char>(buf_[2]), Bytes(buf_.begin() + 3, buf_.begin() + 2 + static_cast<long>(n))};
                    buf_.erase(buf_.begin(), buf_.begin() + 2 + static_cast<long>(n));
                    return f;
                }
            }
            pollfd p{fd_, POLLIN, 0};
            if (::poll(&p, 1, timeout_ms) <= 0) return std::nullopt;
            u8 tmp[65536];
            const ssize_t n = ::recv(fd_, tmp, sizeof tmp, 0);
            if (n <= 0) return std::nullopt;
            buf_.insert(buf_.end(), tmp, tmp + n);
        }
    }
    // The next sequenced application message, skipping heartbeats.
    std::optional<Out> next_report(int timeout_ms) {
        while (auto f = recv(timeout_ms)) {
            if (f->first == 'S') return decode_out(f->second);
        }
        return std::nullopt;
    }
    void close() { if (fd_ >= 0) { ::close(fd_); fd_ = -1; } buf_.clear(); }

private:
    void raw(const Bytes& b) { ::send(fd_, b.data(), b.size(), MSG_NOSIGNAL); }
    int fd_{-1};
    Bytes buf_;
};

class FeedReceiver {
public:
    ~FeedReceiver() { if (fd_ >= 0) ::close(fd_); }
    // Binds a UDP port (0 = ephemeral) and, if `group` is not empty, joins the group on the loopback interface.
    bool open(int port, const std::string& group) {
        fd_ = socket(AF_INET, SOCK_DGRAM, 0);
        const int one = 1;
        setsockopt(fd_, SOL_SOCKET, SO_REUSEADDR, &one, sizeof one);
        sockaddr_in a{};
        a.sin_family = AF_INET;
        a.sin_port = htons(static_cast<u16>(port));
        a.sin_addr.s_addr = htonl(group.empty() ? INADDR_LOOPBACK : INADDR_ANY);
        if (bind(fd_, reinterpret_cast<sockaddr*>(&a), sizeof a) != 0) return false;
        if (!group.empty()) {
            ip_mreq m{};
            inet_pton(AF_INET, group.c_str(), &m.imr_multiaddr);
            inet_pton(AF_INET, "127.0.0.1", &m.imr_interface);
            if (setsockopt(fd_, IPPROTO_IP, IP_ADD_MEMBERSHIP, &m, sizeof m) != 0) return false;
        }
        return true;
    }
    int port() const {
        sockaddr_in a{};
        socklen_t n = sizeof a;
        getsockname(fd_, reinterpret_cast<sockaddr*>(&a), &n);
        return ntohs(a.sin_port);
    }
    std::optional<Bytes> recv(int timeout_ms) {
        pollfd p{fd_, POLLIN, 0};
        if (::poll(&p, 1, timeout_ms) <= 0) return std::nullopt;
        Bytes b(65536);
        const ssize_t n = ::recv(fd_, b.data(), b.size(), 0);
        if (n <= 0) return std::nullopt;
        b.resize(static_cast<std::size_t>(n));
        return b;
    }

private:
    int fd_{-1};
};

}  // namespace firm::exchsim
