#pragma once
// firm.pnl -- position and P&L keeper (build of Chapter 7, One Quant Book 1), C++20.
// Exact part in integers (ledger units); the realised / unrealised split in double.
#include <cstdint>
#include <cstdlib>
#include <stdexcept>
#include <string>
#include <unordered_map>

namespace firm {

enum class Side : int { Buy = 1, Sell = -1 };

struct Position {
    std::int64_t quantity = 0;  // signed
    std::int64_t cash = 0;      // signed sum of trade cash flows
    std::int64_t fees = 0;      // positive = paid
    double avg_cost = 0.0;      // of the open position
    double realised = 0.0;

    void on_fill(Side side, std::int64_t qty, std::int64_t price, std::int64_t fee = 0) {
        if (qty <= 0 || price <= 0 || fee < 0) throw std::invalid_argument("bad fill");
        const std::int64_t signed_qty = static_cast<int>(side) * qty;
        cash -= signed_qty * price;
        fees += fee;
        const bool adding = quantity == 0 || ((quantity > 0) == (signed_qty > 0));
        if (adding) {
            const std::int64_t open = std::llabs(quantity);
            avg_cost = (static_cast<double>(open) * avg_cost + static_cast<double>(qty * price)) /
                       static_cast<double>(open + qty);
            quantity += signed_qty;
            return;
        }
        const std::int64_t closing = qty < std::llabs(quantity) ? qty : std::llabs(quantity);
        const double direction = quantity > 0 ? 1.0 : -1.0;
        realised += direction * static_cast<double>(closing) * (static_cast<double>(price) - avg_cost);
        quantity += signed_qty;
        if (qty > closing) avg_cost = static_cast<double>(price);  // flipped
        else if (quantity == 0) avg_cost = 0.0;
    }

    double unrealised(std::int64_t mark) const {
        return static_cast<double>(quantity) * (static_cast<double>(mark) - avg_cost);
    }
    std::int64_t total(std::int64_t mark) const { return cash + quantity * mark - fees; }
};

class Book {
public:
    void on_fill(const std::string& symbol, Side side, std::int64_t qty, std::int64_t price,
                 std::int64_t fee = 0) {
        positions_[symbol].on_fill(side, qty, price, fee);
    }
    const Position& at(const std::string& symbol) const { return positions_.at(symbol); }
    std::int64_t total(const std::unordered_map<std::string, std::int64_t>& marks) const {
        std::int64_t t = 0;
        for (const auto& [s, p] : positions_) t += p.total(marks.at(s));
        return t;
    }

private:
    std::unordered_map<std::string, Position> positions_;
};

}  // namespace firm
