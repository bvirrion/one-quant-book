// firm.exchsim matching engine (One Quant Book 10, chapter 26), C++20.
// A line-by-line port of firm_exchsim_engine.py: same journal in, byte-identical feed and reports out (checked on
// data/fixture_journal.bin by exchsim_engine_test.cpp). PROTOCOL.md section 4 states the rules. Orders live in a
// stable pool (std::deque) and are referred to by pointer from the book, the containers and the sessions.
#pragma once
#include "exchsim_codec.hpp"
#include "exchsim_json.hpp"

#include <algorithm>
#include <deque>
#include <map>
#include <optional>
#include <set>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

namespace firm::exchsim {

constexpr i64 NANO = 1'000'000'000;
constexpr i64 MAX_QTY = 1'000'000'000;

enum class Where : u8 { None, Book, Stop, Mkt, Close, Peg };

struct Order {
    u64 ref{};
    int side{};
    i64 price{}, qty{};
    bool visible{true};
    u64 seq{};
    u16 session{};
    u64 cl{};
    u32 firm{};
    u16 locate{};
    char tif{'D'}, display{'Y'};
    bool post_only{};
    i64 display_qty{}, reserve{}, min_qty{};
    u16 stp_group{};
    char stp_mode{'N'};
    i64 stop_price{}, limit{};
    Where where{Where::None};
    bool top{};
    i64 remaining() const { return qty + reserve; }
};

// The book of firm_lob.LimitOrderBook: per side a sorted map price -> (displayed queue, hidden queue).
class Book {
public:
    struct Level {
        std::deque<Order*> vis, hid;
    };
    std::map<i64, Level>& side_map(int side) { return side == 1 ? bids_ : asks_; }
    const std::map<i64, Level>& side_map(int side) const { return side == 1 ? bids_ : asks_; }

    void add(Order* o) {
        if (!orders.emplace(o->ref, o).second) throw std::runtime_error("duplicate order reference");
        auto& lv = side_map(o->side)[o->price];
        (o->visible ? lv.vis : lv.hid).push_back(o);
    }
    Order* remove(u64 ref) {
        auto it = orders.find(ref);
        if (it == orders.end()) throw std::runtime_error("remove: unknown reference");
        Order* o = it->second;
        orders.erase(it);
        auto& m = side_map(o->side);
        auto lit = m.find(o->price);
        auto& q = o->visible ? lit->second.vis : lit->second.hid;
        q.erase(std::find(q.begin(), q.end(), o));
        if (lit->second.vis.empty() && lit->second.hid.empty()) m.erase(lit);
        return o;
    }
    void reduce(u64 ref, i64 q) {
        Order* o = orders.at(ref);
        if (q > o->qty || q <= 0) throw std::runtime_error("reduce: bad quantity");
        o->qty -= q;
        if (o->qty == 0) remove(ref);
    }
    std::optional<i64> best(int side) const {
        const auto& m = side_map(side);
        if (m.empty()) return std::nullopt;
        return side == 1 ? m.rbegin()->first : m.begin()->first;
    }
    std::vector<i64> prices(int side) const {
        std::vector<i64> out;
        const auto& m = side_map(side);
        if (side == 1) for (auto it = m.rbegin(); it != m.rend(); ++it) out.push_back(it->first);
        else for (const auto& [p, _] : m) out.push_back(p);
        return out;
    }
    std::vector<Order*> level_orders(int side, i64 p) const {
        std::vector<Order*> out;
        const auto& m = side_map(side);
        auto it = m.find(p);
        if (it == m.end()) return out;
        out.insert(out.end(), it->second.vis.begin(), it->second.vis.end());
        out.insert(out.end(), it->second.hid.begin(), it->second.hid.end());
        return out;
    }
    std::optional<i64> best_visible(int side) const {
        const auto& m = side_map(side);
        if (side == 1) {
            for (auto it = m.rbegin(); it != m.rend(); ++it) if (!it->second.vis.empty()) return it->first;
        } else {
            for (const auto& [p, lv] : m) if (!lv.vis.empty()) return p;
        }
        return std::nullopt;
    }
    std::unordered_map<u64, Order*> orders;

private:
    std::map<i64, Level> bids_, asks_;
};

// ---------------------------------------------------------------------------------------------- order-type rules
inline bool marketable(int side, i64 limit, i64 price) {
    if (limit == 0) return true;
    return side == 1 ? price <= limit : price >= limit;
}
inline bool stp_conflict(const Order& a, const Order& b) {
    return a.stp_group != 0 && a.stp_group == b.stp_group && a.firm == b.firm;
}
struct StpActions { bool cancel_resting, cancel_incoming, decrement; };
inline StpActions stp_actions(char mode) {
    switch (mode) {
        case 'O': return {true, false, false};
        case 'W': return {false, true, false};
        case 'B': return {true, true, false};
        case 'D': return {false, false, true};
        default: return {false, false, false};
    }
}
inline bool stop_triggered(const Order& o, i64 last) {
    if (last <= 0) return false;
    return o.side == 1 ? last >= o.stop_price : last <= o.stop_price;
}
inline std::pair<i64, i64> slice_for_display(const Order& o, i64 rem) {
    if (o.visible && o.display_qty) {
        const i64 shown = std::min(o.display_qty, rem);
        return {shown, rem - shown};
    }
    return {rem, 0};
}
inline bool in(char c, const char* set) { return std::string_view(set).find(c) != std::string_view::npos; }

// Book 1's firm_match.configurable (lmm share 0): top order, a FIFO share, pro rata, leftovers by time.
inline std::vector<i64> configurable(const std::vector<std::pair<i64, bool>>& book, i64 qty, i64 top_pct, i64 fifo_pct,
                                     i64 min_alloc) {
    const std::size_t n = book.size();
    std::vector<i64> fills(n, 0);
    auto take = [&](std::size_t i, i64 want, i64 left) {
        const i64 got = std::min({want, book[i].first - fills[i], left});
        if (got > 0) fills[i] += got;
        return left - std::max<i64>(got, 0);
    };
    i64 total = 0;
    for (const auto& b : book) total += b.first;
    i64 left = std::min(qty, total);
    for (std::size_t i = 0; i < n; ++i) {
        if (book[i].second) { left = take(i, qty * top_pct / 100, left); break; }
    }
    i64 by_time = left * fifo_pct / 100;
    for (std::size_t i = 0; i < n; ++i) {
        if (by_time <= 0) break;
        const i64 before = left;
        left = take(i, by_time, left);
        by_time -= before - left;
    }
    std::vector<i64> open(n);
    i64 tot = 0;
    for (std::size_t i = 0; i < n; ++i) { open[i] = book[i].first - fills[i]; tot += open[i]; }
    left = std::min(left, tot);
    if (left <= 0) return fills;
    const i64 target = left;
    for (std::size_t i = 0; i < n; ++i) {
        const i64 share = target * open[i] / tot;
        if (share >= min_alloc) left = take(i, share, left);
    }
    for (std::size_t i = 0; i < n; ++i) left = take(i, book[i].first, left);
    return fills;
}

// Book 1's firm_auction.uncross: maximum volume, minimum surplus, market pressure, reference price.
struct AuctionOrder { int side; i64 qty; std::optional<i64> price; u64 seq; };
struct Uncrossing {
    std::optional<i64> price;
    i64 volume{}, surplus{};
    std::vector<std::pair<std::size_t, i64>> fills;
};
inline Uncrossing uncross(const std::vector<AuctionOrder>& orders, i64 reference) {
    std::set<i64> ps{reference};
    for (const auto& o : orders) if (o.price) ps.insert(*o.price);
    struct Row { i64 p, d, s; };
    std::vector<Row> table;
    for (i64 p : ps) {
        i64 d = 0, s = 0;
        for (const auto& o : orders) {
            if (o.side > 0 && (!o.price || *o.price >= p)) d += o.qty;
            if (o.side < 0 && (!o.price || *o.price <= p)) s += o.qty;
        }
        table.push_back({p, d, s});
    }
    i64 best = 0;
    for (const auto& r : table) best = std::max(best, std::min(r.d, r.s));
    if (best == 0) return {};
    std::vector<Row> c;
    for (const auto& r : table) if (std::min(r.d, r.s) == best) c.push_back(r);
    i64 least = -1;
    for (const auto& r : c) { const i64 x = r.d > r.s ? r.d - r.s : r.s - r.d; if (least < 0 || x < least) least = x; }
    std::vector<Row> c2;
    for (const auto& r : c) if ((r.d > r.s ? r.d - r.s : r.s - r.d) == least) c2.push_back(r);
    bool all_buy = true, all_sell = true;
    for (const auto& r : c2) { all_buy = all_buy && r.d > r.s; all_sell = all_sell && r.d < r.s; }
    Row pick = c2.front();
    if (all_buy) pick = c2.back();
    else if (all_sell) pick = c2.front();
    else {
        for (const auto& r : c2) {
            const i64 dr = r.p > reference ? r.p - reference : reference - r.p;
            const i64 dp = pick.p > reference ? pick.p - reference : reference - pick.p;
            if (dr < dp || (dr == dp && r.p < pick.p)) pick = r;
        }
    }
    Uncrossing u;
    u.price = pick.p;
    u.volume = best;
    u.surplus = pick.d - pick.s;
    for (int side : {+1, -1}) {
        std::vector<std::size_t> el;
        for (std::size_t i = 0; i < orders.size(); ++i) {
            const auto& o = orders[i];
            if (o.side == side && (!o.price || (side > 0 ? *o.price >= pick.p : *o.price <= pick.p))) el.push_back(i);
        }
        std::stable_sort(el.begin(), el.end(), [&](std::size_t a, std::size_t b) {
            const auto& x = orders[a];
            const auto& y = orders[b];
            const std::tuple<bool, i64, u64> kx{x.price.has_value(), -side * x.price.value_or(0), x.seq};
            const std::tuple<bool, i64, u64> ky{y.price.has_value(), -side * y.price.value_or(0), y.seq};
            return kx < ky;
        });
        i64 left = best;
        for (std::size_t i : el) {
            const i64 q = std::min(left, orders[i].qty);
            if (q) u.fills.emplace_back(i, q);
            left -= q;
        }
    }
    return u;
}

// ---------------------------------------------------------------------------------------------- the engine
struct Trade { u64 match; u16 locate; i64 price, qty; u16 resting_session, aggressor_session; int side; char liquidity; };

class Engine {
public:
    struct Inst {
        u16 locate{};
        Alpha8 symbol;
        i64 tick{}, lot{};
        char matching{'F'};
        i64 top_pct{}, fifo_pct{}, min_alloc{1};
        Book book;
        char phase{'C'};
        i64 ref_price{}, band_lo{}, band_hi{}, last{};
        bool frozen{};
        std::vector<Order*> stops, mkt, close, pegs;
        std::unordered_set<u64> pegged;
        bool has_ref{};
        i64 ref_bid{}, ref_ask{};                 // control N: reference quote for midpoint pegs
    };
    struct Sess {
        u32 firm{};
        bool cod{}, logged{true};
        i64 tokens{};
        bool has_last{};
        u64 last_t{};
        std::unordered_set<u64> used;
        std::unordered_map<u64, Order*> live;
        std::map<u16, std::vector<u64>> quotes;
    };

    explicit Engine(const json::Value& cfg) {
        engine_ns_ = static_cast<u64>(cfg.get_int("engine_ns", 0));
        const auto& f = cfg["fees"];
        fee_bp_ = f["unit"].s == "bp";
        make_ = f["make"].i;
        take_ = f["take"].i;
        cross_ = f["cross"].i;
        if (cfg.has("throttle")) {
            const auto& th = cfg["throttle"];
            rate_ = th["rate"].i;
            burst_ = th["burst"].i;
            if (th.has("weights"))
                for (const auto& [k, v] : th["weights"].o) weights_[k.at(0)] = v.i;
        }
        for (const auto& d : cfg["instruments"].a) {
            Inst st;
            st.locate = static_cast<u16>(d["locate"].i);
            st.symbol = Alpha8(d["symbol"].s);
            st.tick = d["tick"].i;
            st.lot = d["lot"].i;
            st.matching = d.get_str("matching", "F").at(0);
            st.top_pct = d.get_int("top_pct", 0);
            st.fifo_pct = d.get_int("fifo_pct", 0);
            st.min_alloc = d.get_int("min_alloc", 1);
            st.phase = d.get_str("phase", "C").at(0);
            st.ref_price = d.get_int("start_price", 0);
            inst_.emplace(st.locate, std::move(st));
        }
    }

    // One journal record. Outputs are appended to `feed` and `reports` (cleared first).
    void process(u64 t_ns, u16 session, Span payload) {
        feed.clear();
        reports.clear();
        touched_.clear();
        ts = std::max(t_ns, busy_) + engine_ns_;
        busy_ = ts;
        if (session == 0) {
            control(decode_ctl(payload));
        } else {
            auto it = sessions_.find(session);
            if (it != sessions_.end() && it->second.logged) {
                const In m = decode_in(payload);
                const i64 w = weights_.count(m.type) ? weights_[m.type] : 1;
                if (throttled(it->second, t_ns, w)) {
                    u64 cl = 0;
                    if (m.type == 'O' || m.type == 'U' || m.type == 'X') cl = m.cl_ord_id;
                    else if (m.type == 'Q') cl = m.quote_id * 2;
                    rej(session, cl, 'T');
                } else {
                    inbound(session, it->second, m);
                }
            }
        }
        std::vector<u16> locs(touched_.begin(), touched_.end());
        std::sort(locs.begin(), locs.end());
        for (u16 l : locs) settle(inst_.at(l));
    }

    std::vector<Feed> snapshot(u16 locate, u64 seq, u64 at) {
        Inst& st = inst_.at(locate);
        std::vector<Feed> out;
        u32 n = 0;
        for (const auto& [_, o] : st.book.orders) n += o->visible ? 1 : 0;
        Feed g = base('G', locate, at);
        g.seq = seq;
        g.orders = n;
        out.push_back(g);
        Feed h = base('H', locate, at);
        h.stock = st.symbol;
        h.state = state_of(st.phase);
        h.reason = {'S', 'N', 'A', 'P'};
        out.push_back(h);
        Bytes body;
        for (int side : {1, -1}) {
            for (i64 p : st.book.prices(side)) {
                for (Order* o : st.book.level_orders(side, p)) {
                    if (!o->visible) continue;
                    Feed a = base('A', locate, at);
                    a.ref = o->ref;
                    a.side = side == 1 ? 'B' : 'S';
                    a.shares = static_cast<u64>(o->qty);
                    a.stock = st.symbol;
                    a.price = static_cast<u32>(p);
                    encode(body, a);
                    out.push_back(a);
                }
            }
        }
        Feed w = base('W', locate, at);
        w.seq = seq;
        w.crc = crc32(body);
        out.push_back(w);
        return out;
    }

    std::vector<u16> locates() const {
        std::vector<u16> v;
        for (const auto& [k, _] : inst_) v.push_back(k);
        return v;
    }
    const Inst& instrument(u16 locate) const { return inst_.at(locate); }

    std::vector<Feed> feed;
    std::vector<std::pair<u16, Out>> reports;
    std::vector<Trade> trades;
    u64 ts{};

private:
    // -- helpers -----------------------------------------------------------------------------------------------
    static char state_of(char phase) {
        switch (phase) {
            case 'T': return 'T'; case 'H': return 'H'; case 'U': return 'P'; case 'C': return 'C'; default: return 'Q';
        }
    }
    static bool is_call(char phase) { return phase == 'O' || phase == 'K' || phase == 'U' || phase == 'B'; }
    Feed base(char t, u16 locate, u64 at) const {
        Feed m;
        m.type = t;
        m.locate = locate;
        m.ts = at;
        return m;
    }
    bool throttled(Sess& s, u64 t, i64 weight) {
        if (rate_ <= 0) return false;
        const __int128 cap = static_cast<__int128>(burst_) * NANO;
        if (s.has_last) {
            const __int128 refill = static_cast<__int128>(s.tokens) +
                                    static_cast<__int128>(static_cast<i64>(t - s.last_t)) * rate_;
            s.tokens = static_cast<i64>(std::min(cap, refill));
        }
        s.has_last = true;
        s.last_t = t;
        if (s.tokens >= weight * NANO) { s.tokens -= weight * NANO; return false; }
        return true;
    }
    i64 fee(char liq, i64 price, i64 qty) const {
        const i64 rate = liq == 'A' ? make_ : liq == 'R' ? take_ : cross_;
        if (!fee_bp_) return rate * qty;
        const __int128 x = static_cast<__int128>(price) * qty * rate;
        return static_cast<i64>(x / 10000);             // C++ division truncates toward zero, as the spec says
    }
    u64 new_ref() { return next_ref_++; }
    u64 next_seq() { return ++seq_; }
    void rep(u16 session, const Out& m) { reports.emplace_back(session, m); }
    void rej(u16 session, u64 cl, char reason) {
        Out j; j.type = 'J'; j.ts = ts; j.cl_ord_id = cl; j.reason = reason;
        rep(session, j);
    }
    void rep_c(u16 session, u64 cl, i64 dec, char reason) {
        Out c; c.type = 'C'; c.ts = ts; c.cl_ord_id = cl; c.decrement = static_cast<u32>(dec); c.reason = reason;
        rep(session, c);
    }
    void rep_e(u16 session, u64 cl, i64 q, i64 p, u64 m, char liq, i64 f, i64 leaves) {
        Out e; e.type = 'E'; e.ts = ts; e.cl_ord_id = cl; e.qty = static_cast<u32>(q); e.price = static_cast<u32>(p);
        e.match = m; e.liquidity = liq; e.fee = f; e.leaves = static_cast<u32>(leaves);
        rep(session, e);
    }
    void feed_a(const Inst& st, const Order& o, i64 shown, i64 price) {
        Feed a = base('A', st.locate, ts);
        a.ref = o.ref; a.side = o.side == 1 ? 'B' : 'S'; a.shares = static_cast<u64>(shown); a.stock = st.symbol;
        a.price = static_cast<u32>(price);
        feed.push_back(a);
    }
    void feed_d(const Inst& st, u64 ref) { Feed d = base('D', st.locate, ts); d.ref = ref; feed.push_back(d); }
    void feed_x(const Inst& st, u64 ref, i64 q) {
        Feed x = base('X', st.locate, ts); x.ref = ref; x.shares = static_cast<u64>(q); feed.push_back(x);
    }
    void feed_u(const Inst& st, u64 ref, u64 nref, i64 q, i64 p) {
        Feed u = base('U', st.locate, ts); u.ref = ref; u.new_ref = nref; u.shares = static_cast<u64>(q);
        u.price = static_cast<u32>(p);
        feed.push_back(u);
    }
    static void erase_ptr(std::vector<Order*>& v, Order* o) {
        auto it = std::find(v.begin(), v.end(), o);
        if (it != v.end()) v.erase(it);
    }

    void done(Order* o) {
        o->where = Where::None;
        auto& live = sessions_.at(o->session).live;
        auto it = live.find(o->cl);
        if (it != live.end() && it->second == o) live.erase(it);
        erase_ptr(inst_.at(o->locate).pegs, o);
    }
    void remove_from_container(Inst& st, Order* o) {
        switch (o->where) {
            case Where::Book:
                st.book.remove(o->ref);
                st.pegged.erase(o->ref);
                if (o->visible) feed_d(st, o->ref);
                break;
            case Where::Stop: erase_ptr(st.stops, o); break;
            case Where::Mkt: erase_ptr(st.mkt, o); break;
            case Where::Close: erase_ptr(st.close, o); break;
            default: break;
        }
        o->where = Where::None;
    }
    void cancel(Order* o, char reason) {
        Inst& st = inst_.at(o->locate);
        const i64 d = o->remaining();
        remove_from_container(st, o);
        rep_c(o->session, o->cl, d, reason);
        done(o);
        touched_.insert(st.locate);
    }
    void decrement(Order* o, i64 d, char reason) {
        Inst& st = inst_.at(o->locate);
        if (d >= o->remaining()) { cancel(o, reason); return; }
        const i64 from_res = std::min(o->reserve, d);
        o->reserve -= from_res;
        const i64 shown = d - from_res;
        if (shown) {
            if (o->where == Where::Book) {
                st.book.reduce(o->ref, shown);
                if (o->visible) feed_x(st, o->ref, shown);
            } else {
                o->qty -= shown;
            }
        }
        rep_c(o->session, o->cl, d, reason);
        touched_.insert(st.locate);
    }
    void rest(Inst& st, Order* o, i64 rem) {
        auto [shown, reserve] = slice_for_display(*o, rem);
        o->qty = shown;
        o->reserve = reserve;
        const auto best = st.book.best(o->side);
        o->top = !best || (o->side == 1 ? o->price > *best : o->price < *best);
        st.book.add(o);
        o->where = Where::Book;
        if (o->display == 'M' || o->display == 'P') st.pegged.insert(o->ref);
        if (o->visible) feed_a(st, *o, shown, o->price);
    }
    bool would_cross(const Inst& st, int side, i64 lim) const {
        const auto p = st.book.best(-side);
        return p && marketable(side, lim, *p);
    }
    std::optional<i64> peg_target(const Inst& st, const Order& o) const {
        i64 p = 0;
        if (o.display == 'M') {
            if (st.has_ref) {
                p = (st.ref_bid + st.ref_ask) / 2;
            } else {
                const auto b = st.book.best_visible(1), a = st.book.best_visible(-1);
                if (!b || !a) return std::nullopt;
                p = (*b + *a) / 2;
            }
        } else {
            bool found = false;
            for (i64 px : st.book.prices(o.side)) {
                for (Order* x : st.book.level_orders(o.side, px)) {
                    if (x->visible && !st.pegged.count(x->ref)) { found = true; break; }
                }
                if (found) { p = px; break; }
            }
            if (!found) return std::nullopt;
        }
        if (o.limit) p = o.side == 1 ? std::min(p, o.limit) : std::max(p, o.limit);
        return p;
    }

    // -- matching ----------------------------------------------------------------------------------------------
    i64 eligible(const Inst& st, const Order& o, i64 lim, i64 rem) const {
        i64 total = 0;
        for (i64 p : st.book.prices(-o.side)) {
            if (!marketable(o.side, lim, p) || (st.band_hi && !(st.band_lo <= p && p <= st.band_hi))) break;
            for (Order* r : st.book.level_orders(-o.side, p)) {
                if (stp_conflict(o, *r) || (r->min_qty && rem < r->min_qty)) continue;
                total += r->remaining();
            }
        }
        return total;
    }
    void execute(Inst& st, Order* r, Order* o, i64 q, i64 p, i64 rem_after) {
        const u64 m = ++next_match_;
        if (r->visible) {
            Feed e = base('E', st.locate, ts); e.ref = r->ref; e.shares = static_cast<u64>(q); e.match = m;
            feed.push_back(e);
        } else {
            Feed x = base('P', st.locate, ts); x.ref = 0; x.side = r->side == 1 ? 'B' : 'S';
            x.shares = static_cast<u64>(q); x.stock = st.symbol; x.price = static_cast<u32>(p); x.match = m;
            feed.push_back(x);
        }
        st.book.reduce(r->ref, q);
        if (r->qty == 0) {
            st.pegged.erase(r->ref);
            if (r->reserve > 0) {
                const i64 shown = std::min(r->display_qty, r->reserve);
                r->reserve -= shown;
                r->qty = shown;
                r->ref = new_ref();
                r->seq = next_seq();
                r->top = false;
                st.book.add(r);
                feed_a(st, *r, shown, r->price);
            } else {
                r->where = Where::None;
            }
        }
        rep_e(r->session, r->cl, q, p, m, 'A', fee('A', p, q), r->remaining());
        if (r->remaining() == 0) done(r);
        rep_e(o->session, o->cl, q, p, m, 'R', fee('R', p, q), rem_after);
        st.last = p;
        trades.push_back({m, st.locate, p, q, r->session, o->session, o->side, 'R'});
    }
    i64 match(Inst& st, Order* o, i64 lim, i64 rem) {
        const int opp = -o->side;
        for (i64 p : st.book.prices(opp)) {
            if (rem == 0 || !marketable(o->side, lim, p) || (st.band_hi && !(st.band_lo <= p && p <= st.band_hi))) break;
            while (rem > 0) {
                const auto level = st.book.level_orders(opp, p);
                if (level.empty()) break;
                std::vector<Order*> elig;
                for (Order* r : level) {
                    if (stp_conflict(*o, *r) && o->stp_mode != 'N') {
                        const auto a = stp_actions(o->stp_mode);
                        if (a.decrement) {
                            const i64 d = std::min(rem, r->remaining());
                            decrement(r, d, 'S');
                            rem -= d;
                            rep_c(o->session, o->cl, d, 'S');
                            if (rem == 0) return 0;
                            continue;
                        }
                        if (a.cancel_resting) cancel(r, 'S');
                        if (a.cancel_incoming) { rep_c(o->session, o->cl, rem, 'S'); return -1; }
                        continue;
                    }
                    if (r->min_qty && rem < r->min_qty) continue;
                    elig.push_back(r);
                }
                if (elig.empty()) {
                    if (st.book.level_orders(opp, p).size() == level.size()) break;
                    continue;
                }
                std::vector<i64> alloc(elig.size(), 0);
                if (st.matching == 'F') {
                    i64 left = rem;
                    for (std::size_t i = 0; i < elig.size(); ++i) {
                        alloc[i] = std::min(elig[i]->qty, left);
                        left -= alloc[i];
                        if (left == 0) break;
                    }
                } else {
                    std::vector<std::pair<i64, bool>> bk;
                    for (Order* r : elig) bk.emplace_back(r->qty, r->top);
                    alloc = configurable(bk, rem, st.top_pct, st.fifo_pct, st.min_alloc);
                }
                for (std::size_t i = 0; i < elig.size(); ++i) {
                    if (alloc[i] > 0) {
                        rem -= alloc[i];
                        execute(st, elig[i], o, alloc[i], p, rem);
                    }
                }
            }
        }
        return rem;
    }
    void incoming(Inst& st, Order* o, i64 lim, i64 rem) {
        const i64 need = o->tif == 'F' ? rem : o->min_qty;
        if (need && eligible(st, *o, lim, rem) < need) {
            if (o->tif == 'I' || o->tif == 'F') {
                rep_c(o->session, o->cl, rem, 'I');
                done(o);
            } else {
                o->price = lim;
                rest(st, o, rem);
            }
            return;
        }
        rem = match(st, o, lim, rem);
        if (rem <= 0) {
            if (rem == 0) { o->qty = 0; o->reserve = 0; }
            done(o);
            return;
        }
        if (lim == 0 || o->tif == 'I' || o->tif == 'F') {
            rep_c(o->session, o->cl, rem, 'I');
            done(o);
            return;
        }
        o->price = lim;
        rest(st, o, rem);
    }

    // -- order entry -------------------------------------------------------------------------------------------
    char validate(const In& m, const Inst& st) const {
        if (st.phase == 'C' || st.phase == 'H') return 'H';
        if (m.qty == 0 || m.qty > MAX_QTY || m.display_qty > m.qty) return 'Q';
        if (!in(m.side, "BS") || !in(m.tif, "DGIFOC") || !in(m.display, "YNMP") || !in(m.stp_mode, "NOWBD")) return 'Q';
        if (m.min_qty && !(m.tif == 'I' || m.display == 'M')) return 'Q';
        if (m.display_qty && m.display != 'Y') return 'Q';
        if (m.price % st.tick || m.stop_price % st.tick) return 'X';
        if (m.tif == 'O' && st.phase != 'O') return 'H';
        if (m.tif == 'C' && (st.frozen || !in(st.phase, "TKO"))) return st.frozen ? 'C' : 'H';
        if (m.price && st.band_hi && !(st.band_lo <= static_cast<i64>(m.price) && m.price <= st.band_hi)) return 'B';
        return 0;
    }
    Order* accept(u16 session, Sess& s, const In& m) {
        pool_.emplace_back();
        Order* o = &pool_.back();
        o->ref = new_ref();
        o->side = m.side == 'B' ? 1 : -1;
        o->price = m.price;
        o->qty = m.qty;
        o->visible = m.display == 'Y' || m.display == 'P';
        o->session = session;
        o->cl = m.cl_ord_id;
        o->firm = s.firm;
        o->locate = m.locate;
        o->tif = m.tif;
        o->display = m.display;
        o->post_only = m.post_only == 'Y';
        o->display_qty = m.display_qty;
        o->min_qty = m.min_qty;
        o->stp_group = m.stp_group;
        o->stp_mode = m.stp_mode;
        o->stop_price = m.stop_price;
        o->limit = m.price;
        o->seq = next_seq();
        s.used.insert(m.cl_ord_id);
        s.live[m.cl_ord_id] = o;
        Out a; a.type = 'A'; a.ts = ts; a.cl_ord_id = m.cl_ord_id; a.ref = o->ref; a.locate = m.locate; a.side = m.side;
        a.qty = m.qty; a.price = m.price; a.tif = m.tif; a.display = m.display; a.state = m.stop_price ? 'S' : 'L';
        rep(session, a);
        return o;
    }
    void enter(u16 session, Sess& s, const In& m) {
        auto it = inst_.find(m.locate);
        if (it == inst_.end()) { rej(session, m.cl_ord_id, 'S'); return; }
        Inst& st = it->second;
        if (s.used.count(m.cl_ord_id)) { rej(session, m.cl_ord_id, 'D'); return; }
        char why = validate(m, st);
        if (!why && m.post_only == 'Y' && st.phase == 'T' && !m.stop_price && (m.display == 'Y' || m.display == 'N') &&
            would_cross(st, m.side == 'B' ? 1 : -1, m.price))
            why = 'O';
        if (why) { rej(session, m.cl_ord_id, why); return; }
        touched_.insert(st.locate);
        Order* o = accept(session, s, m);
        if (m.stop_price) { o->where = Where::Stop; st.stops.push_back(o); return; }
        if (m.tif == 'C') { o->where = Where::Close; st.close.push_back(o); return; }
        if (m.display == 'M' || m.display == 'P') { st.pegs.push_back(o); o->where = Where::Peg; return; }
        if (is_call(st.phase)) { to_call(st, o); return; }
        incoming(st, o, o->limit, o->qty);
    }
    void to_call(Inst& st, Order* o) {
        if (o->tif == 'I' || o->tif == 'F') {
            rep_c(o->session, o->cl, o->remaining(), 'I');
            done(o);
        } else if (o->limit == 0) {
            o->where = Where::Mkt;
            st.mkt.push_back(o);
        } else {
            o->price = o->limit;
            rest(st, o, o->remaining());
        }
    }
    void inbound(u16 session, Sess& s, const In& m) {
        switch (m.type) {
            case 'O': enter(session, s, m); break;
            case 'X': in_cancel(session, s, m); break;
            case 'M': in_mass(s, m); break;
            case 'U': in_replace(session, s, m); break;
            case 'Q': in_quote(session, s, m); break;
            default: break;
        }
    }
    void in_cancel(u16 session, Sess& s, const In& m) {
        auto it = s.live.find(m.cl_ord_id);
        if (it == s.live.end()) { rej(session, m.cl_ord_id, 'L'); return; }
        Order* o = it->second;
        if (static_cast<i64>(m.leave_qty) >= o->remaining()) return;
        if (m.leave_qty == 0) cancel(o, 'U');
        else decrement(o, o->remaining() - m.leave_qty, 'U');
    }
    static std::vector<Order*> by_seq(const std::unordered_map<u64, Order*>& live) {
        std::vector<Order*> v;
        for (const auto& [_, o] : live) v.push_back(o);
        std::sort(v.begin(), v.end(), [](Order* a, Order* b) { return a->seq < b->seq; });
        return v;
    }
    void in_mass(Sess& s, const In& m) {
        const int side = m.side == 'B' ? 1 : m.side == 'S' ? -1 : 0;
        for (Order* o : by_seq(s.live))
            if ((m.locate == 0 || o->locate == m.locate) && (side == 0 || o->side == side)) cancel(o, 'M');
    }
    void in_replace(u16 session, Sess& s, const In& m) {
        auto it = s.live.find(m.cl_ord_id);
        if (it == s.live.end()) { rej(session, m.cl_ord_id, 'L'); return; }
        Order* o = it->second;
        Inst& st = inst_.at(o->locate);
        if (s.used.count(m.new_cl_ord_id)) { rej(session, m.new_cl_ord_id, 'D'); return; }
        char why = 0;
        if (st.phase == 'C' || st.phase == 'H') why = 'H';
        else if (m.qty == 0 || m.qty > MAX_QTY) why = 'Q';
        else if (m.price % st.tick || ((m.price == 0) != (o->limit == 0))) why = 'X';
        else if (m.price && st.band_hi && !(st.band_lo <= static_cast<i64>(m.price) && m.price <= st.band_hi)) why = 'B';
        else if (o->post_only && st.phase == 'T' && o->where == Where::Book && o->display != 'M' && o->display != 'P' &&
                 static_cast<i64>(m.price) != o->limit && would_cross(st, o->side, m.price))
            why = 'O';
        if (why) { rej(session, m.new_cl_ord_id, why); return; }
        touched_.insert(st.locate);
        s.used.insert(m.new_cl_ord_id);
        s.live.erase(o->cl);
        const u64 old_cl = o->cl;
        o->cl = m.new_cl_ord_id;
        s.live[o->cl] = o;
        Out u; u.type = 'U'; u.ts = ts; u.cl_ord_id = old_cl; u.new_cl_ord_id = o->cl; u.qty = m.qty; u.price = m.price;
        if (static_cast<i64>(m.price) == o->limit && static_cast<i64>(m.qty) <= o->remaining() && o->where != Where::None) {
            const i64 d = o->remaining() - m.qty;
            if (d) {
                const i64 from_res = std::min(o->reserve, d);
                o->reserve -= from_res;
                const i64 shown = d - from_res;
                if (shown) {
                    if (o->where == Where::Book) {
                        st.book.reduce(o->ref, shown);
                        if (o->visible) feed_x(st, o->ref, shown);
                    } else {
                        o->qty -= shown;
                    }
                }
            }
            u.ref = o->ref;
            u.priority = 'Y';
            rep(session, u);
            return;
        }
        const bool was_book = o->where == Where::Book;
        const bool vis = o->visible;
        const u64 old_ref = o->ref;
        if (was_book) {
            st.book.remove(o->ref);
            st.pegged.erase(o->ref);
            o->where = Where::None;
        }
        o->limit = m.price;
        o->seq = next_seq();
        o->qty = m.qty;
        o->reserve = 0;
        if (was_book) o->ref = new_ref();
        u.ref = o->ref;
        u.priority = 'N';
        rep(session, u);
        if (!was_book) return;
        if (o->display == 'M' || o->display == 'P') {
            if (vis) feed_d(st, old_ref);
            o->where = Where::Peg;
            return;
        }
        if (st.phase == 'T' && would_cross(st, o->side, o->limit)) {
            if (vis) feed_d(st, old_ref);
            incoming(st, o, o->limit, o->qty);
            return;
        }
        o->price = o->limit;
        auto [shown, reserve] = slice_for_display(*o, o->qty);
        o->qty = shown;
        o->reserve = reserve;
        o->top = false;
        st.book.add(o);
        o->where = Where::Book;
        if (vis) feed_u(st, old_ref, o->ref, shown, o->price);
    }
    void in_quote(u16 session, Sess& s, const In& m) {
        auto it = inst_.find(m.locate);
        if (it == inst_.end()) { rej(session, m.quote_id * 2, 'S'); return; }
        auto qit = s.quotes.find(m.locate);
        if (qit != s.quotes.end()) {
            const auto ids = qit->second;
            s.quotes.erase(qit);
            for (u64 cl : ids) {
                auto lit = s.live.find(cl);
                if (lit != s.live.end()) cancel(lit->second, 'U');
            }
        }
        std::vector<u64> ids;
        const std::array<std::tuple<u64, char, u32, u32>, 2> legs{
            std::tuple{m.quote_id * 2, 'B', m.bid_price, m.bid_qty},
            std::tuple{m.quote_id * 2 + 1, 'S', m.ask_price, m.ask_qty}};
        for (const auto& [cl, side, px, qty] : legs) {
            if (qty == 0) continue;
            ids.push_back(cl);
            In o;
            o.type = 'O'; o.cl_ord_id = cl; o.locate = m.locate; o.side = side; o.qty = qty; o.price = px;
            enter(session, s, o);
        }
        s.quotes[m.locate] = ids;
    }

    // -- settle ------------------------------------------------------------------------------------------------
    void settle(Inst& st) {
        bool stuck = false;
        for (int iter = 0; iter < 64; ++iter) {
            bool changed = false;
            if (st.phase == 'T') {
                std::vector<Order*> trig;
                for (Order* o : st.stops) if (stop_triggered(*o, st.last)) trig.push_back(o);
                for (Order* o : trig) {
                    if (o->where != Where::Stop) continue;
                    erase_ptr(st.stops, o);
                    o->where = Where::None;
                    o->stop_price = 0;
                    if (o->display == 'M' || o->display == 'P') {
                        st.pegs.push_back(o);
                        o->where = Where::Peg;
                    } else {
                        incoming(st, o, o->limit, o->qty);
                    }
                    changed = true;
                }
                const std::vector<Order*> pegs = st.pegs;
                for (Order* o : pegs) {
                    if (o->where != Where::Book && o->where != Where::Peg) continue;
                    const auto target = peg_target(st, *o);
                    if (o->where == Where::Book && target && *target == o->price) continue;
                    if (o->where == Where::Peg && !target) continue;
                    changed = true;
                    const u64 old_ref = o->ref;
                    const bool vis = o->visible;
                    if (o->where == Where::Book) {
                        st.book.remove(o->ref);
                        st.pegged.erase(o->ref);
                        const i64 rem = o->remaining();
                        o->qty = rem;
                        o->reserve = 0;
                        if (!target) {
                            o->where = Where::Peg;
                            if (vis) feed_d(st, old_ref);
                            continue;
                        }
                        o->where = Where::None;
                        if (would_cross(st, o->side, *target)) {
                            if (vis) { feed_d(st, old_ref); o->ref = new_ref(); }
                            incoming(st, o, *target, rem);
                            continue;
                        }
                        o->price = *target;
                        o->top = false;
                        if (vis) o->ref = new_ref();
                        st.book.add(o);
                        st.pegged.insert(o->ref);
                        o->where = Where::Book;
                        if (vis) feed_u(st, old_ref, o->ref, o->qty, o->price);
                    } else {
                        o->where = Where::None;
                        incoming(st, o, *target, o->qty);
                    }
                }
                const auto b = st.book.best(1), a = st.book.best(-1);
                if (b && a && *b >= *a && !stuck) {
                    const std::size_t before = trades.size();
                    Order* rb = st.book.level_orders(1, *b).front();
                    Order* ra = st.book.level_orders(-1, *a).front();
                    Order* agg = rb->seq > ra->seq ? rb : ra;
                    const i64 rem = agg->remaining();
                    st.book.remove(agg->ref);
                    st.pegged.erase(agg->ref);
                    if (agg->visible) { feed_d(st, agg->ref); agg->ref = new_ref(); }
                    agg->qty = rem;
                    agg->reserve = 0;
                    agg->where = Where::None;
                    incoming(st, agg, agg->price, rem);
                    if (trades.size() == before) stuck = true;
                    changed = true;
                }
            }
            if (!changed) return;
        }
        throw std::runtime_error("settle did not converge");
    }

    // -- auctions ----------------------------------------------------------------------------------------------
    std::vector<Order*> auction_orders(Inst& st, char cross_type) {
        std::vector<Order*> out;
        for (int side : {1, -1})
            for (i64 p : st.book.prices(side))
                for (Order* o : st.book.level_orders(side, p))
                    if (o->display != 'M' && o->display != 'P') out.push_back(o);
        out.insert(out.end(), st.mkt.begin(), st.mkt.end());
        if (cross_type == 'C') out.insert(out.end(), st.close.begin(), st.close.end());
        return out;
    }
    Uncrossing uncross_calc(Inst& st, char cross_type, std::vector<Order*>& orders) {
        orders = auction_orders(st, cross_type);
        std::vector<AuctionOrder> ao;
        for (Order* o : orders)
            ao.push_back({o->side, o->remaining(), o->limit ? std::optional<i64>(o->limit) : std::nullopt, o->seq});
        return uncross(ao, st.ref_price ? st.ref_price : st.last);
    }
    void do_uncross(Inst& st, char cross_type) {
        std::vector<Order*> orders;
        const Uncrossing u = uncross_calc(st, cross_type, orders);
        touched_.insert(st.locate);
        if (u.volume > 0) {
            const u64 m = ++next_match_;
            const i64 p = *u.price;
            for (const auto& [idx, q] : u.fills) {
                Order* o = orders[idx];
                if (o->where == Where::Book) {
                    const i64 shown = std::min(q, o->qty);
                    if (o->visible) {
                        Feed c = base('C', st.locate, ts); c.ref = o->ref; c.shares = static_cast<u64>(shown); c.match = m;
                        c.printable = 'N'; c.price = static_cast<u32>(p);
                        feed.push_back(c);
                    }
                    st.book.reduce(o->ref, shown);
                    o->reserve -= q - shown;
                    if (o->qty == 0 && o->reserve > 0) {
                        const i64 s2 = std::min(o->display_qty, o->reserve);
                        o->reserve -= s2;
                        o->qty = s2;
                        o->ref = new_ref();
                        o->seq = next_seq();
                        o->top = false;
                        st.book.add(o);
                        feed_a(st, *o, s2, o->price);
                    } else if (o->qty == 0) {
                        o->where = Where::None;
                    }
                } else {
                    o->qty -= q;
                    if (o->qty == 0) {
                        erase_ptr(o->where == Where::Mkt ? st.mkt : st.close, o);
                        o->where = Where::None;
                    }
                }
                rep_e(o->session, o->cl, q, p, m, 'C', fee('C', p, q), o->remaining());
                if (o->remaining() == 0) done(o);
                trades.push_back({m, st.locate, p, q, o->session, 0, o->side, 'C'});
            }
            Feed x = base('Q', st.locate, ts); x.shares = static_cast<u64>(u.volume); x.stock = st.symbol;
            x.price = static_cast<u32>(p); x.match = m; x.cross_type = cross_type;
            feed.push_back(x);
            st.last = p;
            st.ref_price = p;
        }
        std::vector<Order*> left(st.mkt.begin(), st.mkt.end());
        if (cross_type == 'O')
            for (int side : {1, -1})
                for (i64 px : st.book.prices(side))
                    for (Order* o : st.book.level_orders(side, px))
                        if (o->tif == 'O') left.push_back(o);
        if (cross_type == 'C') left.insert(left.end(), st.close.begin(), st.close.end());
        std::stable_sort(left.begin(), left.end(), [](Order* a, Order* b) { return a->seq < b->seq; });
        for (Order* o : left)
            if (o->where != Where::None) cancel(o, o->where == Where::Mkt ? 'I' : 'E');
    }

    // -- control -----------------------------------------------------------------------------------------------
    std::vector<Inst*> scope(u16 locate) {
        std::vector<Inst*> v;
        if (locate == 0) for (auto& [_, st] : inst_) v.push_back(&st);
        else v.push_back(&inst_.at(locate));
        return v;
    }
    void control(const Ctl& m) {
        switch (m.type) {
            case 'L': {
                auto it = sessions_.find(m.session);
                if (it == sessions_.end()) {
                    Sess s;
                    s.firm = m.firm;
                    s.cod = m.cod == 'Y';
                    s.tokens = burst_ * NANO;
                    sessions_.emplace(m.session, std::move(s));
                } else {
                    it->second.logged = true;
                    it->second.cod = m.cod == 'Y';
                }
                break;
            }
            case 'D': {
                auto it = sessions_.find(m.session);
                if (it == sessions_.end()) break;
                it->second.logged = false;
                if (it->second.cod)
                    for (Order* o : by_seq(it->second.live)) cancel(o, 'D');
                break;
            }
            case 'P':
                for (Inst* st : scope(m.locate)) {
                    const char old = st->phase;
                    st->phase = m.phase;
                    Feed h = base('H', st->locate, ts);
                    h.stock = st->symbol; h.state = state_of(m.phase); h.reserved = ' '; h.reason = m.reason;
                    feed.push_back(h);
                    touched_.insert(st->locate);
                    if (is_call(old) && (m.phase == 'T' || m.phase == 'C') && old != m.phase) {
                        const char ct = old == 'O' ? 'O' : old == 'K' ? 'C' : old == 'U' ? 'H' : 'B';
                        do_uncross(*st, ct);
                    } else if (old == 'T' && m.phase == 'C') {
                        do_uncross(*st, 'C');
                    }
                }
                break;
            case 'X':
                for (Inst* st : scope(m.locate)) do_uncross(*st, m.cross_type);
                break;
            case 'I':
                for (Inst* st : scope(m.locate)) {
                    std::vector<Order*> orders;
                    const Uncrossing u = uncross_calc(*st, m.cross_type, orders);
                    Feed x = base('I', st->locate, ts);
                    x.paired = static_cast<u64>(u.volume);
                    x.imbalance = static_cast<u64>(u.surplus < 0 ? -u.surplus : u.surplus);
                    x.direction = u.volume == 0 ? 'O' : u.surplus > 0 ? 'B' : u.surplus < 0 ? 'S' : 'N';
                    const i64 p = u.volume == 0 ? 0 : *u.price;
                    x.stock = st->symbol; x.far = static_cast<u32>(p); x.nearp = static_cast<u32>(p);
                    x.ref_price = static_cast<u32>(st->ref_price); x.cross_type = m.cross_type; x.variation = ' ';
                    feed.push_back(x);
                }
                break;
            case 'R': {
                Inst& st = inst_.at(m.locate);
                st.ref_price = m.ref_price;
                st.band_lo = m.band_lo;
                st.band_hi = m.band_hi;
                break;
            }
            case 'N': {
                Inst& st = inst_.at(m.locate);
                st.has_ref = m.bid > 0 && m.ask > 0;
                st.ref_bid = st.has_ref ? m.bid : 0;
                st.ref_ask = st.has_ref ? m.ask : 0;
                touched_.insert(st.locate);
                break;
            }
            case 'E': {
                std::vector<Order*> v;
                for (auto& [_, s] : sessions_)
                    for (auto& [__, o] : s.live)
                        if ((m.locate == 0 || o->locate == m.locate) && (m.tif == 'A' || o->tif != 'G')) v.push_back(o);
                std::sort(v.begin(), v.end(), [](Order* a, Order* b) { return a->seq < b->seq; });
                for (Order* o : v) cancel(o, 'E');
                break;
            }
            case 'F':
                for (Inst* st : scope(m.locate)) st->frozen = m.freeze == 'Y';
                break;
            case 'S': {
                Feed s = base('S', 0, ts);
                s.event = m.event;
                feed.push_back(s);
                if (m.event == 'O') {
                    for (Inst* st : scope(0)) {
                        Feed r = base('R', st->locate, ts);
                        r.stock = st->symbol; r.tick = static_cast<u32>(st->tick); r.lot = static_cast<u32>(st->lot);
                        r.matching = st->matching;
                        feed.push_back(r);
                    }
                }
                for (auto& [sid, sess] : sessions_) {
                    if (!sess.logged) continue;
                    Out o; o.type = 'S'; o.ts = ts; o.event = m.event;
                    rep(sid, o);
                }
                break;
            }
            default: break;
        }
    }

    std::map<u16, Inst> inst_;
    std::map<u16, Sess> sessions_;
    std::deque<Order> pool_;
    std::set<u16> touched_;
    std::map<char, i64> weights_;
    u64 engine_ns_{}, busy_{}, next_ref_{1}, next_match_{}, seq_{};
    i64 rate_{}, burst_{}, make_{}, take_{}, cross_{};
    bool fee_bp_{};
};

}  // namespace firm::exchsim
