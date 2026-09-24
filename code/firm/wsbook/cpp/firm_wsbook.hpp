// firm.wsbook -- websocket order-book builder (build of Chapter 26, One Quant Book 3), C++20 twin of
// firm_wsbook.py: snapshot plus (U, u)-numbered deltas with absolute quantities, gap detection and
// resync, and a CRC32 checksum over the ten best asks (low to high) then bids (high to low).
#pragma once
#include <cstdint>
#include <functional>
#include <map>
#include <string>
#include <utility>
#include <vector>

namespace firm::wsbook {

using Levels = std::vector<std::pair<std::int64_t, std::int64_t>>;
enum class Status { ignored, applied, gap };

inline std::uint32_t crc32(const std::string& s) {
    std::uint32_t c = 0xFFFFFFFFu;
    for (unsigned char byte : s) {
        c ^= byte;
        for (int k = 0; k < 8; ++k) c = (c >> 1) ^ ((c & 1u) ? 0xEDB88320u : 0u);
    }
    return c ^ 0xFFFFFFFFu;
}

class Book {
public:
    void snapshot(std::int64_t id, const Levels& bids, const Levels& asks) {
        bids_.clear();
        asks_.clear();
        for (auto [p, q] : bids) bids_[p] = q;
        for (auto [p, q] : asks) asks_[p] = q;
        update_id_ = id;
        synced_ = true;
    }

    Status apply(std::int64_t first, std::int64_t last, const Levels& bids, const Levels& asks) {
        if (!synced_) return Status::gap;
        if (last < update_id_ + 1) return Status::ignored;
        if (first > update_id_ + 1) {
            synced_ = false;
            return Status::gap;
        }
        for (auto [p, q] : bids) q == 0 ? void(bids_.erase(p)) : void(bids_[p] = q);
        for (auto [p, q] : asks) q == 0 ? void(asks_.erase(p)) : void(asks_[p] = q);
        update_id_ = last;
        return Status::applied;
    }

    [[nodiscard]] std::uint32_t checksum() const {
        std::string s;
        int n = 0;
        for (auto it = asks_.begin(); it != asks_.end() && n < 10; ++it, ++n)
            s += std::to_string(it->first) + std::to_string(it->second);
        n = 0;
        for (auto it = bids_.begin(); it != bids_.end() && n < 10; ++it, ++n)
            s += std::to_string(it->first) + std::to_string(it->second);
        return crc32(s);
    }

    [[nodiscard]] bool synced() const { return synced_; }
    [[nodiscard]] std::int64_t update_id() const { return update_id_; }
    [[nodiscard]] const std::map<std::int64_t, std::int64_t, std::greater<>>& bids() const { return bids_; }
    [[nodiscard]] const std::map<std::int64_t, std::int64_t>& asks() const { return asks_; }

private:
    std::map<std::int64_t, std::int64_t, std::greater<>> bids_;
    std::map<std::int64_t, std::int64_t> asks_;
    std::int64_t update_id_ = -1;
    bool synced_ = false;
};

}  // namespace firm::wsbook
