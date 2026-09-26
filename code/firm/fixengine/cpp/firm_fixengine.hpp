// firm.fixengine -- FIX tag=value codec and session layer in C++20 (build of One Quant Book 13, chapter 15).
// The codec never allocates: a View records (tag, offset, length) for each field of a message it does not copy, and
// a Builder writes into its own fixed buffer. The Session reproduces the Python reference's trace byte for byte on
// the golden conversation (data/expected_trace.txt); its message store and out-of-order queue allocate, off the
// path of a message received in sequence.
#pragma once
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <map>
#include <string>
#include <string_view>
#include <vector>

#include "../../simdscan/cpp/firm_simdscan.hpp"

namespace firm::fix {

constexpr char SOH = '\x01';

inline unsigned checksum(const char* p, std::size_t n) {
    unsigned s = 0;
    for (std::size_t i = 0; i < n; ++i) s += static_cast<unsigned char>(p[i]);
    return s % 256;
}

enum class Error { ok, framing, tag, order, body_length, checksum, too_many_fields };

struct FieldRef {
    int tag;
    std::uint32_t off, len;
};

// A parsed message: views into the caller's buffer, which must outlive it.
class View {
public:
    static constexpr std::size_t kMaxFields = 128;

    Error parse(const char* p, std::size_t n) {
        p_ = p;
        n_ = n;
        count_ = 0;
        if (n < 5 || p[0] != '8' || p[1] != '=' || p[n - 1] != SOH) return Error::framing;
        std::uint32_t soh[kMaxFields];
        const std::size_t k = simdscan::positions(p, n, SOH, soh, kMaxFields);
        if (k == kMaxFields && soh[k - 1] != n - 1) return Error::too_many_fields;
        std::size_t start = 0;
        for (std::size_t i = 0; i < k; ++i) {
            std::uint64_t tag = 0;
            std::size_t used = 0;
            if (!simdscan::parse_uint(p + start, soh[i] - start, tag, used) || p[start + used] != '=') return Error::tag;
            fields_[count_++] = FieldRef{static_cast<int>(tag), static_cast<std::uint32_t>(start + used + 1),
                                         static_cast<std::uint32_t>(soh[i] - start - used - 1)};
            start = soh[i] + 1;
        }
        if (count_ < 4 || fields_[0].tag != 8 || fields_[1].tag != 9 || fields_[2].tag != 35 ||
            fields_[count_ - 1].tag != 10)
            return Error::order;
        for (std::size_t i = 3; i + 1 < count_; ++i)  // found by chapter 25's fuzzer: a CheckSum inside the body
            if (fields_[i].tag == 10 || fields_[i].tag == 8 || fields_[i].tag == 9) return Error::order;
        const std::size_t body_start = fields_[1].off + fields_[1].len + 1;
        const std::size_t body_end = fields_[count_ - 1].off - 3;          // first byte of "10="
        std::uint64_t declared = 0;
        std::size_t used = 0;
        simdscan::parse_uint(p + fields_[1].off, fields_[1].len, declared, used);
        if (used != fields_[1].len || declared != body_end - body_start) return Error::body_length;
        const std::string_view ck = value(count_ - 1);
        std::uint64_t c = 0;
        if (ck.size() != 3 || !simdscan::parse_uint(ck.data(), 3, c, used) || used != 3 || c != checksum(p, body_end))
            return Error::checksum;
        return Error::ok;
    }

    std::size_t size() const { return count_; }
    int tag(std::size_t i) const { return fields_[i].tag; }
    std::string_view value(std::size_t i) const { return {p_ + fields_[i].off, fields_[i].len}; }
    std::string_view get(int tag, std::string_view dflt = {}) const {
        for (std::size_t i = 0; i < count_; ++i)
            if (fields_[i].tag == tag) return value(i);
        return dflt;
    }
    std::string_view msg_type() const { return value(2); }
    std::int64_t seq() const {
        const auto v = get(34);
        std::uint64_t s = 0;
        std::size_t used = 0;
        simdscan::parse_uint(v.data(), v.size(), s, used);
        return static_cast<std::int64_t>(s);
    }
    std::string_view raw() const { return {p_, n_}; }

private:
    const char* p_ = nullptr;
    std::size_t n_ = 0, count_ = 0;
    std::array<FieldRef, kMaxFields> fields_{};
};

// Length of the first complete message at p (0 if more bytes are needed; err set on garbage).
inline std::size_t frame(const char* p, std::size_t n, Error& err) {
    err = Error::ok;
    if (n < 2) return 0;
    if (p[0] != '8' || p[1] != '=') { err = Error::framing; return 0; }
    const std::size_t a = simdscan::find_byte(p, n, SOH);
    if (a == n || n < a + 3) return 0;
    if (p[a + 1] != '9' || p[a + 2] != '=') { err = Error::framing; return 0; }
    const std::size_t b = a + 1 + simdscan::find_byte(p + a + 1, n - a - 1, SOH);
    if (b >= n) return 0;
    std::uint64_t body = 0;
    std::size_t used = 0;
    simdscan::parse_uint(p + a + 3, b - a - 3, body, used);
    const std::size_t total = b + 1 + body + 7;
    return n >= total ? total : 0;
}

inline std::string sending_time(std::int64_t now_ms) {
    const std::int64_t s = now_ms / 1000, ms = now_ms % 1000;
    char b[32];
    std::snprintf(b, sizeof b, "20260925-%02d:%02d:%02d.%03d", static_cast<int>(s / 3600), static_cast<int>(s % 3600 / 60),
                  static_cast<int>(s % 60), static_cast<int>(ms));
    return b;
}

// Decimal digits of v at p; returns the count. (snprintf would cost more than the rest of a field.)
inline std::size_t put_uint(char* p, std::uint64_t v) {
    char t[20];
    std::size_t k = 0;
    do {
        t[k++] = static_cast<char>('0' + v % 10);
        v /= 10;
    } while (v != 0);
    for (std::size_t i = 0; i < k; ++i) p[i] = t[k - 1 - i];
    return k;
}

inline void put2(char* p, int v) {
    p[0] = static_cast<char>('0' + v / 10);
    p[1] = static_cast<char>('0' + v % 10);
}

// Writes a message into a fixed buffer: the body first, at an offset that leaves room for "8=...|9=...|" in front,
// then the header right-aligned against it, then the checksum. No allocation and no formatted output.
class Builder {
public:
    explicit Builder(std::string_view begin = "FIX.4.4") : begin_(begin) {}

    Builder& start(std::string_view msg_type, std::int64_t seq, std::string_view sender, std::string_view target,
                   std::int64_t now_ms) {
        pos_ = kReserve;
        add(35, msg_type).add(49, sender).add(56, target).add(34, seq);
        char t[22] = "20260925-00:00:00.000";
        const std::int64_t s = now_ms / 1000;
        put2(t + 9, static_cast<int>(s / 3600));
        put2(t + 12, static_cast<int>(s % 3600 / 60));
        put2(t + 15, static_cast<int>(s % 60));
        t[18] = static_cast<char>('0' + now_ms % 1000 / 100);
        put2(t + 19, static_cast<int>(now_ms % 100));
        return add(52, std::string_view(t, 21));
    }
    Builder& add(int tag, std::string_view v) {
        pos_ += put_uint(buf_.data() + pos_, static_cast<std::uint64_t>(tag));
        buf_[pos_++] = '=';
        std::memcpy(buf_.data() + pos_, v.data(), v.size());
        pos_ += v.size();
        buf_[pos_++] = SOH;
        return *this;
    }
    Builder& add(int tag, std::int64_t v) {
        pos_ += put_uint(buf_.data() + pos_, static_cast<std::uint64_t>(tag));
        buf_[pos_++] = '=';
        if (v < 0) {
            buf_[pos_++] = '-';
            v = -v;
        }
        pos_ += put_uint(buf_.data() + pos_, static_cast<std::uint64_t>(v));
        buf_[pos_++] = SOH;
        return *this;
    }
    Builder& add_raw(std::string_view fields) {   // already encoded "tag=value<SOH>..." fields
        if (fields.empty()) return *this;
        std::memcpy(buf_.data() + pos_, fields.data(), fields.size());
        pos_ += fields.size();
        return *this;
    }
    std::string_view finish() {
        char head[48] = "8=";
        std::size_t h = 2;
        std::memcpy(head + h, begin_.data(), begin_.size());
        h += begin_.size();
        head[h++] = SOH;
        head[h++] = '9';
        head[h++] = '=';
        h += put_uint(head + h, pos_ - kReserve);
        head[h++] = SOH;
        const std::size_t first = kReserve - h;
        std::memcpy(buf_.data() + first, head, h);
        const unsigned c = checksum(buf_.data() + first, pos_ - first);
        char* q = buf_.data() + pos_;
        q[0] = '1';
        q[1] = '0';
        q[2] = '=';
        q[3] = static_cast<char>('0' + c / 100);
        put2(q + 4, static_cast<int>(c % 100));
        q[6] = SOH;
        pos_ += 7;
        return {buf_.data() + first, pos_ - first};
    }

private:
    static constexpr std::size_t kReserve = 48;
    std::string_view begin_;
    std::array<char, 8192> buf_{};
    std::size_t pos_ = kReserve;
};

inline bool is_admin(std::string_view t) {
    return t == "0" || t == "1" || t == "2" || t == "3" || t == "4" || t == "5" || t == "A";
}

inline std::string printable(std::string_view raw) {
    std::string s(raw);
    for (auto& c : s)
        if (c == SOH) c = '|';
    return s;
}

// The session layer of one connection, with the Python reference's rules and trace.
class Session {
public:
    Session(std::string sender, std::string target, int heartbeat_s = 30)
        : sender_(std::move(sender)), target_(std::move(target)), hb_(heartbeat_s) {}

    std::string state = "disconnected";
    std::int64_t next_out = 1, next_in = 1;
    std::vector<std::string> trace;          // every event, as the Python reference prints it
    std::vector<std::string> out;            // outgoing messages of the last call
    std::vector<std::string> delivered;      // application messages delivered by the last call

    void logon(std::int64_t now) {
        out.clear();
        state = "logon_sent";
        last_recv_ = now;
        emit("A", field(98, "0") + field(108, std::to_string(hb_)), now);
    }
    void send(std::string_view type, std::string_view body, std::int64_t now) {
        out.clear();
        emit(type, body, now);
    }
    void logout(std::int64_t now, std::string_view text = {}) {
        out.clear();
        state = "logout_sent";
        emit("5", text.empty() ? std::string() : field(58, text), now);
    }

    Error on_bytes(const char* p, std::size_t n, std::int64_t now) {
        out.clear();
        delivered.clear();
        View m;
        if (const Error e = m.parse(p, n); e != Error::ok) return e;
        last_recv_ = now;
        const auto t = m.msg_type();
        if (t == "4" && m.get(123, "N") != "Y") {
            next_in = to_int(m.get(36));
            log(now, "reset next_in=" + std::to_string(next_in));
            return Error::ok;
        }
        const std::int64_t seq = m.seq();
        if (seq > next_in) {
            if (t == "2") resend(m, now);
            queue_[seq] = std::string(p, n);
            if (!resend_asked_) {
                resend_asked_ = true;
                log(now, "gap expected=" + std::to_string(next_in) + " received=" + std::to_string(seq));
                emit("2", field(7, std::to_string(next_in)) + field(16, "0"), now);
            }
            return Error::ok;
        }
        if (seq < next_in) {
            if (m.get(43) == "Y") {
                log(now, "duplicate " + std::to_string(seq) + " ignored");
                return Error::ok;
            }
            log(now, "seq " + std::to_string(seq) + " too low, expected " + std::to_string(next_in));
            state = "logout_sent";
            emit("5", field(58, "MsgSeqNum too low, expecting " + std::to_string(next_in) + " but received " +
                                    std::to_string(seq)), now);
            disconnect(now, "sequence too low");
            return Error::ok;
        }
        process(m, now);
        while (queue_.count(next_in) != 0) {
            const std::string q = queue_[next_in];
            queue_.erase(next_in);
            View v;
            v.parse(q.data(), q.size());
            if (v.msg_type() == "2") ++next_in;
            else process(v, now);
        }
        if (resend_asked_ && queue_.empty()) {
            resend_asked_ = false;
            log(now, "gap closed next_in=" + std::to_string(next_in));
        }
        return Error::ok;
    }

    void on_timer(std::int64_t now) {
        out.clear();
        if (state != "active" && state != "logout_sent") return;
        const std::int64_t hb = hb_ * 1000LL;
        if (!test_id_.empty() && now - test_sent_ >= hb) {
            disconnect(now, "no answer to test request");
            return;
        }
        if (test_id_.empty() && now - last_recv_ >= hb + hb / 5) {
            test_id_ = "TEST" + std::to_string(++tests_);
            test_sent_ = now;
            emit("1", field(112, test_id_), now);
        } else if (now - last_sent_ >= hb) {
            emit("0", "", now);
        }
    }

private:
    struct Stored {
        std::string type, body;
        std::int64_t sent;
    };

    static std::string field(int tag, std::string_view v) {
        return std::to_string(tag) + "=" + std::string(v) + SOH;
    }
    static std::int64_t to_int(std::string_view v) {
        std::uint64_t x = 0;
        std::size_t used = 0;
        simdscan::parse_uint(v.data(), v.size(), x, used);
        return static_cast<std::int64_t>(x);
    }
    void log(std::int64_t now, const std::string& s) { trace.push_back(std::to_string(now) + " " + s); }
    void disconnect(std::int64_t now, const char* why) {
        state = "disconnected";
        log(now, std::string("state disconnected (") + why + ")");
    }

    // header: extra header fields after 52 (43, 122), already encoded
    void emit(std::string_view type, std::string_view body, std::int64_t now, std::int64_t seq = 0,
              std::string_view header = {}) {
        const bool fresh = seq == 0;
        if (fresh) seq = next_out;
        builder_.start(type, seq, sender_, target_, now).add_raw(header).add_raw(body);
        const std::string_view raw = builder_.finish();
        if (fresh) {
            store_[seq] = Stored{std::string(type), std::string(body), now};
            ++next_out;
        }
        last_sent_ = now;
        out.emplace_back(raw);
        log(now, "out " + printable(raw));
    }

    void process(const View& m, std::int64_t now) {
        const auto t = m.msg_type();
        if (t == "4") {
            next_in = to_int(m.get(36));
            log(now, "gap fill to " + std::to_string(next_in));
            return;
        }
        ++next_in;
        if (t == "A") {
            if (state == "logon_sent") {
                state = "active";
                log(now, "state active");
            }
        } else if (t == "0") {
            if (!test_id_.empty() && m.get(112) == test_id_) test_id_.clear();
        } else if (t == "1") {
            emit("0", field(112, m.get(112)), now);
        } else if (t == "2") {
            resend(m, now);
        } else if (t == "5") {
            if (state != "logout_sent") emit("5", "", now);
            disconnect(now, "logout");
        } else if (!is_admin(t)) {
            delivered.emplace_back(m.raw());
            log(now, "deliver " + std::to_string(m.seq()) + " " + std::string(t));
        }
    }

    void resend(const View& m, std::int64_t now) {
        const std::int64_t lo = to_int(m.get(7));
        std::int64_t hi = to_int(m.get(16));
        if (hi == 0 || hi >= next_out) hi = next_out - 1;
        std::int64_t gap = 0;
        const std::string dup = field(43, "Y");
        for (std::int64_t s = lo; s <= hi; ++s) {
            const auto it = store_.find(s);
            if (it == store_.end() || is_admin(it->second.type)) {
                if (gap == 0) gap = s;
                continue;
            }
            if (gap != 0) {
                emit("4", field(123, "Y") + field(36, std::to_string(s)), now, gap, dup);
                gap = 0;
            }
            emit(it->second.type, it->second.body, now, s, dup + field(122, sending_time(it->second.sent)));
        }
        if (gap != 0) emit("4", field(123, "Y") + field(36, std::to_string(hi + 1)), now, gap, dup);
    }

    std::string sender_, target_;
    int hb_;
    Builder builder_;
    std::map<std::int64_t, Stored> store_;
    std::map<std::int64_t, std::string> queue_;
    std::int64_t last_sent_ = 0, last_recv_ = 0, test_sent_ = 0;
    std::string test_id_;
    int tests_ = 0;
    bool resend_asked_ = false;
};

}  // namespace firm::fix
