// firm.quoteengine -- from target quotes to orders (One Quant Book 11, chapter 10), C++20 twin of
// firm_quoteengine.QuoteEngine: same rules, same order of decisions, same action log on data/fixture_*.csv.
#pragma once

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <limits>
#include <map>
#include <optional>
#include <string>
#include <utility>
#include <vector>

namespace firm {

class TokenBucket {
public:
    TokenBucket(double rate, double burst) : rate_(rate), burst_(burst), tokens_(burst) {}
    bool take(double t) {
        if (std::isinf(rate_)) return true;
        if (t_) tokens_ = std::min(burst_, tokens_ + rate_ * (t - *t_));
        t_ = t;
        if (tokens_ >= 1.0) {
            tokens_ -= 1.0;
            return true;
        }
        return false;
    }

private:
    double rate_, burst_, tokens_;
    std::optional<double> t_;
};

enum class State { PendingNew, Live, PendingAmend, PendingCancel };

struct Order {
    int oid;
    int side;
    std::int64_t price;
    std::int64_t leaves;
    State state;
};

struct Action {
    enum Kind { New, Amend, Cancel } kind;
    int oid;
    int side = 0;
    std::int64_t price = 0;
    std::int64_t qty = 0;
    [[nodiscard]] std::string str() const {
        if (kind == New)
            return "new " + std::to_string(oid) + " " + std::to_string(side) + " " + std::to_string(price) + " " +
                   std::to_string(qty);
        if (kind == Amend) return "amend " + std::to_string(oid) + " " + std::to_string(qty);
        return "cancel " + std::to_string(oid);
    }
};

struct Stats {
    long new_ = 0, amend = 0, cancel = 0, dropped = 0, fills = 0, races = 0;
};

class QuoteEngine {
public:
    QuoteEngine(int min_move, std::int64_t min_size, double rate, double burst)
        : min_move_(min_move), min_size_(min_size), bucket_(rate, burst) {}

    std::vector<Action> update(double t, int side, const std::vector<std::pair<std::int64_t, std::int64_t>>& in) {
        std::vector<std::pair<std::int64_t, std::int64_t>> tg;
        for (const auto& x : in)
            if (x.second > 0) tg.push_back(x);
        std::vector<bool> covered(tg.size(), false);
        std::vector<Action> cancels, amends;
        std::vector<std::pair<std::int64_t, std::int64_t>> news;
        std::vector<Order> mine;
        for (const auto& [id, o] : orders_)
            if (o.side == side) mine.push_back(o);
        std::sort(mine.begin(), mine.end(), [side](const Order& a, const Order& b) {
            return std::make_pair(-side * a.price, a.oid) < std::make_pair(-side * b.price, b.oid);
        });
        for (const auto& o : mine) {
            if (o.state != State::Live) {
                if (o.state != State::PendingCancel)
                    for (std::size_t k = 0; k < tg.size(); ++k)
                        if (!covered[k] && tg[k].first == o.price) {
                            covered[k] = true;
                            break;
                        }
                continue;
            }
            std::optional<std::size_t> hit;
            for (std::size_t k = 0; k < tg.size(); ++k)
                if (!covered[k] && tg[k].first == o.price) {
                    hit = k;
                    break;
                }
            if (hit) {
                covered[*hit] = true;
                const auto q = tg[*hit].second;
                if (o.leaves - q >= min_size_) amends.push_back({Action::Amend, o.oid, 0, 0, q});
                else if (q - o.leaves >= min_size_) news.emplace_back(o.price, q - o.leaves);
                continue;
            }
            std::optional<std::size_t> best;
            for (std::size_t k = 0; k < tg.size(); ++k) {
                if (covered[k] || std::llabs(tg[k].first - o.price) >= min_move_) continue;
                if (!best || std::llabs(tg[k].first - o.price) < std::llabs(tg[*best].first - o.price)) best = k;
            }
            if (best) {
                covered[*best] = true;
                continue;
            }
            cancels.push_back({Action::Cancel, o.oid});
        }
        for (std::size_t k = 0; k < tg.size(); ++k)
            if (!covered[k]) news.push_back(tg[k]);
        std::vector<Action> out;
        cancels.insert(cancels.end(), amends.begin(), amends.end());
        for (const auto& a : cancels) {
            if (!bucket_.take(t)) {
                ++stats.dropped;
                continue;
            }
            auto& o = orders_.at(a.oid);
            if (a.kind == Action::Cancel) {
                o.state = State::PendingCancel;
                ++stats.cancel;
            } else {
                o.state = State::PendingAmend;
                o.leaves = a.qty;
                ++stats.amend;
            }
            out.push_back(a);
        }
        for (const auto& [p, q] : news) {
            if (!bucket_.take(t)) {
                ++stats.dropped;
                continue;
            }
            ++next_;
            orders_[next_] = Order{next_, side, p, q, State::PendingNew};
            ++stats.new_;
            out.push_back({Action::New, next_, side, p, q});
        }
        return out;
    }

    void ack(int oid) {
        auto it = orders_.find(oid);
        if (it == orders_.end()) return;
        if (it->second.state == State::PendingCancel) orders_.erase(it);
        else it->second.state = State::Live;
    }

    void fill(int oid, std::int64_t qty) {
        auto it = orders_.find(oid);
        if (it == orders_.end()) return;
        ++stats.fills;
        if (it->second.state == State::PendingCancel) ++stats.races;
        it->second.leaves -= qty;
        if (it->second.leaves <= 0) orders_.erase(it);
    }

    Stats stats;

private:
    int min_move_;
    std::int64_t min_size_;
    TokenBucket bucket_;
    std::map<int, Order> orders_;
    int next_ = 0;
};

}  // namespace firm
