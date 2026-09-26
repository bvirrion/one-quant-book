// firm.binlog (C++20): binary logging with deferred formatting, and the input journal (build of One Quant Book 13,
// chapter 23).
//
// A log statement is `log.log<"fill {} at {}">(ts, qty, price)`. Its format string and argument types are template
// arguments, so its identifier is computed at compile time (a 16-bit FNV-1a hash of both) and the statement registers
// itself before main(); on the hot path a call writes the identifier, a timestamp and the raw arguments into a
// single-producer ring (firm.ring) and returns. A writer thread drains the ring into a file whose header lists every
// statement; formatting happens offline, in the Python decoder (firm_binlog.py). A full ring drops the record and
// counts it: the hot path never waits.
//
// File:    "FBINLOG1" | u32 n | n x (u16 id | u8 ntypes | types | u16 fmtlen | fmt), sorted by id | records
// Record:  u16 id | u16 payload bytes | u32 0 | u64 ts | payload   (little-endian)
// Types:   'i' int64, 'u' uint64, 'd' double (8 bytes each), 'c' char (1), 's' string (u8 length + at most 16)
//
// Journal: "FJOURNL1" | u32 record size (56) | records of u64 receive time + the 48-byte event of firm.feedhandler
#pragma once
#include <algorithm>
#include <atomic>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <map>
#include <stdexcept>
#include <string>
#include <string_view>
#include <thread>
#include <type_traits>
#include <vector>

#include "../../ring/cpp/firm_ring.hpp"

namespace firm::binlog {

template <std::size_t N>
struct Fmt {
    char s[N];
    constexpr Fmt(const char (&a)[N]) {  // NOLINT: implicit from a string literal, by design
        for (std::size_t i = 0; i < N; ++i) s[i] = a[i];
    }
    constexpr std::size_t size() const { return N - 1; }
};

template <class T>
constexpr char type_code() {
    using U = std::decay_t<T>;
    if constexpr (std::is_same_v<U, char>) return 'c';
    else if constexpr (std::is_floating_point_v<U>) return 'd';
    else if constexpr (std::is_integral_v<U> && std::is_signed_v<U>) return 'i';
    else if constexpr (std::is_integral_v<U>) return 'u';
    else return 's';  // std::string_view, const char*
}

template <class T>
constexpr std::size_t max_size() {
    constexpr char c = type_code<T>();
    return c == 'c' ? 1 : c == 's' ? 17 : 8;
}

inline constexpr std::size_t kSlot = 64, kHead = 16, kMaxPayload = kSlot - 4 - kHead;

// The statement's identifier: FNV-1a over the format and the type codes, folded to 16 bits.
template <Fmt F, class... A>
constexpr std::uint16_t site_id() {
    std::uint32_t h = 2166136261u;
    for (std::size_t i = 0; i < F.size(); ++i) h = (h ^ static_cast<unsigned char>(F.s[i])) * 16777619u;
    h = (h ^ 0u) * 16777619u;
    ((h = (h ^ static_cast<unsigned char>(type_code<A>())) * 16777619u), ...);
    return static_cast<std::uint16_t>(h ^ (h >> 16));
}

struct SiteInfo {
    std::string fmt, types;
};

inline std::map<std::uint16_t, SiteInfo>& registry() {
    static std::map<std::uint16_t, SiteInfo> r;
    return r;
}

inline bool add_site(std::uint16_t id, std::string fmt, std::string types) {
    auto [it, fresh] = registry().emplace(id, SiteInfo{fmt, types});
    if (!fresh && (it->second.fmt != fmt || it->second.types != types))
        throw std::logic_error("binlog: two statements hash to the same identifier: " + fmt);
    return true;
}

// One per statement: registered during static initialisation, before main().
template <Fmt F, class... A>
struct Site {
    static inline const bool registered = add_site(site_id<F, A...>(), std::string(F.s, F.size()),
                                                   std::string{type_code<A>()...});
};

inline std::uint8_t* put(std::uint8_t* p, std::uint64_t v) {
    std::memcpy(p, &v, 8);
    return p + 8;
}
template <class T>
std::uint8_t* encode(std::uint8_t* p, const T& v) {
    constexpr char c = type_code<T>();
    if constexpr (c == 'c') {
        *p = static_cast<std::uint8_t>(v);
        return p + 1;
    } else if constexpr (c == 'd') {
        const double d = v;
        std::memcpy(p, &d, 8);
        return p + 8;
    } else if constexpr (c == 'i' || c == 'u') {
        return put(p, static_cast<std::uint64_t>(v));
    } else {
        const std::string_view s(v);
        const std::size_t n = std::min<std::size_t>(s.size(), 16);
        *p = static_cast<std::uint8_t>(n);
        std::memcpy(p + 1, s.data(), n);
        return p + 1 + n;
    }
}

// The hot-path half: a ring and an encoder. Not thread-safe: one logger per producing thread.
class Logger {
public:
    explicit Logger(std::uint64_t capacity = 1 << 16) : mem_(region(capacity)), ring_(mem_.data()) {}

    template <Fmt F, class... A>
    bool log(std::uint64_t ts, const A&... a) {
        static_assert((max_size<A>() + ... + 0) <= kMaxPayload, "binlog: arguments too large");
        constexpr std::uint16_t id = site_id<F, A...>();
        (void)Site<F, A...>::registered;
        std::uint8_t rec[kSlot - 4];
        std::uint8_t* p = rec + kHead;
        ((p = encode(p, a)), ...);
        const auto n = static_cast<std::uint16_t>(p - rec - kHead);
        std::memcpy(rec, &id, 2);
        std::memcpy(rec + 2, &n, 2);
        std::memset(rec + 4, 0, 4);
        std::memcpy(rec + 8, &ts, 8);
        if (ring_.try_write(rec, static_cast<std::uint32_t>(kHead + n))) return true;
        dropped_.fetch_add(1, std::memory_order_relaxed);
        return false;
    }

    // The consumer half: append every available record to out; returns how many.
    std::size_t drain(std::vector<std::uint8_t>& out) {
        std::uint8_t rec[kSlot];
        std::size_t k = 0;
        for (int n; (n = ring_.try_read(rec, sizeof rec)) >= 0; ++k) out.insert(out.end(), rec, rec + n);
        return k;
    }
    std::uint64_t dropped() const { return dropped_.load(std::memory_order_relaxed); }

private:
    static std::vector<std::uint8_t> region(std::uint64_t capacity) {
        std::vector<std::uint8_t> v(ring::region_size(capacity, kSlot));
        ring::format(v.data(), capacity, kSlot);
        return v;
    }
    std::vector<std::uint8_t> mem_;
    ring::Spsc ring_;
    std::atomic<std::uint64_t> dropped_{0};
};

// The file header: every registered statement, sorted by identifier.
inline std::vector<std::uint8_t> header() {
    std::vector<std::uint8_t> h{'F', 'B', 'I', 'N', 'L', 'O', 'G', '1'};
    auto put16 = [&](std::uint16_t v) { h.push_back(v & 0xff), h.push_back(v >> 8); };
    const auto n = static_cast<std::uint32_t>(registry().size());
    for (int i = 0; i < 4; ++i) h.push_back(static_cast<std::uint8_t>(n >> (8 * i)));
    for (const auto& [id, s] : registry()) {
        put16(id);
        h.push_back(static_cast<std::uint8_t>(s.types.size()));
        h.insert(h.end(), s.types.begin(), s.types.end());
        put16(static_cast<std::uint16_t>(s.fmt.size()));
        h.insert(h.end(), s.fmt.begin(), s.fmt.end());
    }
    return h;
}

// The writer thread: drains the logger into a file until stopped, then drains what is left.
class Writer {
public:
    Writer(Logger& log, const std::string& path) : log_(log), f_(std::fopen(path.c_str(), "wb")) {
        if (!f_) throw std::runtime_error("binlog: cannot open " + path);
        const auto h = header();
        std::fwrite(h.data(), 1, h.size(), f_);
        th_ = std::thread([this] { loop(); });
    }
    ~Writer() { stop(); }
    void stop() {
        if (!th_.joinable()) return;
        run_.store(false, std::memory_order_release);
        th_.join();
        flush();
        std::fclose(f_);
    }
    std::uint64_t records() const { return records_; }

private:
    std::size_t flush() {
        buf_.clear();
        const std::size_t n = log_.drain(buf_);
        records_ += n;
        if (!buf_.empty()) std::fwrite(buf_.data(), 1, buf_.size(), f_);
        return n;
    }
    // Drain in batches and sleep in between: a writer that polls the ring without pause keeps
    // pulling its cache lines away from the producer, and every log call pays for it.
    void loop() {
        buf_.reserve(1 << 20);
        while (run_.load(std::memory_order_acquire))
            if (flush() < 1024) std::this_thread::sleep_for(std::chrono::microseconds(100));
    }
    Logger& log_;
    std::FILE* f_;
    std::vector<std::uint8_t> buf_;
    std::atomic<bool> run_{true};
    std::uint64_t records_ = 0;
    std::thread th_;
};

// The input journal: fixed-size records, receive time first, written by the thread that receives the inputs.
struct Journal {
    static constexpr std::size_t kRecord = 56;
    std::vector<std::uint8_t> bytes{'F', 'J', 'O', 'U', 'R', 'N', 'L', '1', 56, 0, 0, 0};
    void add(std::uint64_t recv_ts, const std::uint8_t* event48) {
        std::uint8_t r[kRecord];
        std::memcpy(r, &recv_ts, 8);
        std::memcpy(r + 8, event48, 48);
        bytes.insert(bytes.end(), r, r + kRecord);
    }
    static std::vector<std::pair<std::uint64_t, const std::uint8_t*>> records(const std::vector<std::uint8_t>& b) {
        if (b.size() < 12 || std::memcmp(b.data(), "FJOURNL1", 8) != 0) throw std::runtime_error("not a journal");
        std::vector<std::pair<std::uint64_t, const std::uint8_t*>> out;
        for (std::size_t i = 12; i + kRecord <= b.size(); i += kRecord) {
            std::uint64_t t;
            std::memcpy(&t, &b[i], 8);
            out.emplace_back(t, &b[i + 8]);
        }
        return out;
    }
};

}  // namespace firm::binlog
