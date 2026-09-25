// firm.lobreplay core (One Quant Book 7, chapter 18): the 'fifo' queue-position model for shadow orders on a
// market-by-order stream. Reproduces firm_lobreplay.track_fifo: arrivals and cancellations take effect before any
// market message at the same time; a shadow joins behind the orders resting at its price, moves up as those are
// executed or cancelled, and fills when an execution reaches an order behind it.
#pragma once
#include <algorithm>
#include <deque>
#include <map>
#include <tuple>
#include <unordered_map>
#include <utility>
#include <vector>

namespace firm {

struct Msg { double t; char kind; long oid; int side; long price; long qty; };
struct VOrder { int vid; int side; long price; long qty; double arrive; double cancel; };
struct Fill { int vid; double t; long qty; };

class Book {
  public:
    void apply(const Msg& m) {
        if (m.kind == 'A') {
            levels_[m.side][m.price].push_back({m.oid, m.qty});
            where_[m.oid] = {m.side, m.price};
            return;
        }
        auto [side, px] = where_.at(m.oid);
        auto& q = levels_[side][px];
        for (auto it = q.begin(); it != q.end(); ++it) {
            if (it->first == m.oid) {
                it->second -= m.qty;
                if (it->second <= 0) { q.erase(it); where_.erase(m.oid); }
                break;
            }
        }
        if (q.empty()) levels_[side].erase(px);
    }
    const std::deque<std::pair<long, long>>* level(int side, long px) const {
        auto s = levels_.find(side);
        if (s == levels_.end()) return nullptr;
        auto l = s->second.find(px);
        return l == s->second.end() ? nullptr : &l->second;
    }

  private:
    std::map<int, std::map<long, std::deque<std::pair<long, long>>>> levels_;
    std::unordered_map<long, std::pair<int, long>> where_;
};

struct Shadow {
    VOrder o;
    long filled = 0;
    int status = 0;                                     // 0 sent, 1 working, 2 filled, 3 cancelled
    std::unordered_map<long, long> ahead;              // order id -> shares still ahead of us
};

inline std::vector<Fill> track_fifo(const std::vector<Msg>& msgs, const std::vector<VOrder>& orders) {
    std::vector<Shadow> sh;
    for (const auto& o : orders) sh.push_back(Shadow{o, 0, 0, {}});
    std::vector<std::tuple<double, int, int>> ev;       // time, kind (0 arrive, 1 cancel), vid
    for (const auto& o : orders) {
        ev.emplace_back(o.arrive, 0, o.vid);
        if (o.cancel < 1e300) ev.emplace_back(o.cancel, 1, o.vid);
    }
    std::sort(ev.begin(), ev.end());
    Book book;
    std::vector<Fill> out;
    std::map<int, Shadow*> active;                      // ordered by vid, like the Python dict's insertion order
    std::vector<int> order_seen;                        // activation order, to iterate as Python does
    size_t j = 0;
    for (const auto& m : msgs) {
        while (j < ev.size() && std::get<0>(ev[j]) <= m.t) {
            auto [t, kind, vid] = ev[j];
            Shadow& s = sh[vid];
            if (kind == 0 && s.status == 0) {
                s.status = 1;
                if (const auto* q = book.level(s.o.side, s.o.price))
                    for (const auto& [oid, n] : *q) s.ahead[oid] = n;
                active[vid] = &s;
                order_seen.push_back(vid);
            } else if (kind == 1 && s.status <= 1) {
                s.status = 3;
                active.erase(vid);
            }
            ++j;
        }
        std::vector<int> now;
        for (int v : order_seen) if (active.count(v)) now.push_back(v);
        for (int v : now) {
            Shadow& s = sh[v];
            if (s.o.side != m.side || s.o.price != m.price || m.kind == 'A') continue;
            auto it = s.ahead.find(m.oid);
            if (it != s.ahead.end()) {
                it->second -= std::min(m.qty, it->second);
                if (it->second <= 0) s.ahead.erase(it);
            } else if (m.kind == 'E') {
                long q = std::min(s.o.qty - s.filled, m.qty);
                if (q > 0) {
                    s.filled += q;
                    out.push_back({v, m.t, q});
                    if (s.filled >= s.o.qty) { s.status = 2; active.erase(v); }
                }
            }
        }
        book.apply(m);
    }
    return out;
}

}  // namespace firm
