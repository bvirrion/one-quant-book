// firm.ratelimit -- weight-based rate-limit governor (build of Chapter 15, One Quant Book 3), C++20
// twin of firm_ratelimit.py. Fixed windows aligned on the epoch; a request consumes its weight in the
// weight rules and one unit in the order rules if it is an order; 429 and 418 block until retry-after.
#pragma once
#include <cstdint>
#include <string>
#include <utility>
#include <vector>

namespace firm::ratelimit {

enum class Kind { weight, orders };

struct Rule {
    Kind kind;
    std::int64_t interval_ms;
    std::int64_t limit;
    std::int64_t window = -1;
    std::int64_t used = 0;

    [[nodiscard]] std::int64_t room(std::int64_t now) const {
        return now / interval_ms != window ? limit : limit - used;
    }
    void consume(std::int64_t now, std::int64_t units) {
        const std::int64_t w = now / interval_ms;
        if (w != window) {
            window = w;
            used = 0;
        }
        used += units;
    }
    [[nodiscard]] std::int64_t wait_ms(std::int64_t now) const {
        return (now / interval_ms + 1) * interval_ms - now;
    }
};

class Governor {
public:
    explicit Governor(std::vector<Rule> rules) : rules_(std::move(rules)) {}

    // (allowed, milliseconds to wait if not)
    std::pair<bool, std::int64_t> try_send(std::int64_t now, std::int64_t weight, bool is_order) {
        if (now < blocked_until_) return {false, blocked_until_ - now};
        for (const auto& r : rules_) {
            const std::int64_t need = r.kind == Kind::weight ? weight : (is_order ? 1 : 0);
            if (need > 0 && r.room(now) < need) return {false, r.wait_ms(now)};
        }
        for (auto& r : rules_) {
            const std::int64_t need = r.kind == Kind::weight ? weight : (is_order ? 1 : 0);
            if (need > 0) r.consume(now, need);
        }
        return {true, 0};
    }

    void on_status(std::int64_t now, int status, std::int64_t retry_after_ms) {
        if (status == 429 || status == 418) {
            if (now + retry_after_ms > blocked_until_) blocked_until_ = now + retry_after_ms;
            log_.push_back(std::to_string(status) + "@" + std::to_string(now));
        }
    }

    [[nodiscard]] const std::vector<std::string>& log() const { return log_; }

private:
    std::vector<Rule> rules_;
    std::int64_t blocked_until_ = 0;
    std::vector<std::string> log_;
};

inline Governor binance_like() {
    return Governor({{Kind::weight, 60'000, 6'000}, {Kind::orders, 10'000, 100}, {Kind::orders, 86'400'000, 200'000}});
}

}  // namespace firm::ratelimit
