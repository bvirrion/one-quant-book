// Chapter 3 of One Quant Book 14: what the kernel's receive path costs, on loopback.
// A sender thread sends N 64-byte UDP datagrams, each carrying its send time (CLOCK_REALTIME, ns); the receiver
// reads them in one of three ways and records, per datagram, the send time, the kernel's software receive
// timestamp (SO_TIMESTAMPING, taken "when data enters the kernel") and the application's time after the read.
//   mode 0  blocking recvmsg: the thread sleeps in the kernel and is woken for each datagram
//   mode 1  busy polling: non-blocking recvmsg in a loop (MSG_DONTWAIT), the thread never sleeps
//   mode 2  batching: recvmmsg of up to 16 datagrams per call, blocking; the sender sends bursts of 16
#pragma once
#include <arpa/inet.h>
#include <linux/net_tstamp.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>

#include <atomic>
#include <cstdint>
#include <cstring>
#include <ctime>
#include <thread>
#include <vector>

namespace nw_rx {

inline std::int64_t now_ns() {
    timespec ts{};
    clock_gettime(CLOCK_REALTIME, &ts);
    return std::int64_t(ts.tv_sec) * 1'000'000'000 + ts.tv_nsec;
}

struct Sample { std::int64_t sent, kernel, app; };

inline int bound_socket(std::uint16_t* port) {
    int fd = socket(AF_INET, SOCK_DGRAM, 0);
    sockaddr_in a{};
    a.sin_family = AF_INET;
    a.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    a.sin_port = 0;
    if (fd < 0 || bind(fd, reinterpret_cast<sockaddr*>(&a), sizeof a) != 0) return -1;
    socklen_t len = sizeof a;
    getsockname(fd, reinterpret_cast<sockaddr*>(&a), &len);
    *port = ntohs(a.sin_port);
    int flags = SOF_TIMESTAMPING_RX_SOFTWARE | SOF_TIMESTAMPING_SOFTWARE;
    setsockopt(fd, SOL_SOCKET, SO_TIMESTAMPING, &flags, sizeof flags);
    int rcv = 1 << 20;
    setsockopt(fd, SOL_SOCKET, SO_RCVBUF, &rcv, sizeof rcv);
    return fd;
}

inline std::int64_t kernel_stamp(msghdr& m) {
    for (cmsghdr* c = CMSG_FIRSTHDR(&m); c; c = CMSG_NXTHDR(&m, c)) {
        if (c->cmsg_level == SOL_SOCKET && c->cmsg_type == SO_TIMESTAMPING) {
            timespec ts[3];
            std::memcpy(ts, CMSG_DATA(c), sizeof ts);
            return std::int64_t(ts[0].tv_sec) * 1'000'000'000 + ts[0].tv_nsec;
        }
    }
    return 0;
}

// Runs one experiment; gap_ns is the pause between sends (or between bursts in mode 2).
inline std::vector<Sample> run(int mode, int n, std::int64_t gap_ns) {
    std::uint16_t port = 0;
    const int rx = bound_socket(&port);
    const int tx = socket(AF_INET, SOCK_DGRAM, 0);
    std::vector<Sample> out;
    if (rx < 0 || tx < 0) return out;
    out.reserve(n);
    sockaddr_in dst{};
    dst.sin_family = AF_INET;
    dst.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    dst.sin_port = htons(port);
    std::atomic<bool> ready{false};
    std::thread sender([&] {
        while (!ready.load()) {}
        char buf[64] = {};
        for (int i = 0; i < n; ++i) {
            const std::int64_t t = now_ns();
            std::memcpy(buf, &t, sizeof t);
            sendto(tx, buf, sizeof buf, 0, reinterpret_cast<sockaddr*>(&dst), sizeof dst);
            if (mode != 2 || (i + 1) % 16 == 0) {
                const std::int64_t until = now_ns() + gap_ns;
                while (now_ns() < until) {}
            }
        }
    });
    constexpr int kBatch = 16;
    char data[kBatch][64];
    char ctrl[kBatch][256];
    iovec iov[kBatch];
    mmsghdr mm[kBatch];
    for (int k = 0; k < kBatch; ++k) {
        iov[k] = {data[k], sizeof data[k]};
        std::memset(&mm[k], 0, sizeof mm[k]);
        mm[k].msg_hdr.msg_iov = &iov[k];
        mm[k].msg_hdr.msg_iovlen = 1;
        mm[k].msg_hdr.msg_control = ctrl[k];
        mm[k].msg_hdr.msg_controllen = sizeof ctrl[k];
    }
    ready.store(true);
    while (static_cast<int>(out.size()) < n) {
        int got = 0;
        if (mode == 2) {
            for (int k = 0; k < kBatch; ++k) mm[k].msg_hdr.msg_controllen = sizeof ctrl[k];
            got = recvmmsg(rx, mm, kBatch, 0, nullptr);
        } else {
            mm[0].msg_hdr.msg_controllen = sizeof ctrl[0];
            const ssize_t r = recvmsg(rx, &mm[0].msg_hdr, mode == 1 ? MSG_DONTWAIT : 0);
            got = r > 0 ? 1 : 0;
        }
        const std::int64_t app = now_ns();
        for (int k = 0; k < got; ++k) {
            std::int64_t sent = 0;
            std::memcpy(&sent, data[k], sizeof sent);
            out.push_back({sent, kernel_stamp(mm[k].msg_hdr), app});
        }
    }
    sender.join();
    close(rx);
    close(tx);
    return out;
}

}  // namespace nw_rx
