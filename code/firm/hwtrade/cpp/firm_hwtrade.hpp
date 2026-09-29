// firm.hwtrade (C++20): the cycle model of hdl/hwt_trigger.sv (One Quant Book 14, chapter 7). Every register of the
// design is a member; step() applies one clock edge in the order of the design's always_ff block, so the model emits
// the same orders on the same cycles as the HDL in Verilator and Icarus and as the Python CycleModel.
#pragma once
#include <cstdint>
#include <optional>
#include <vector>

namespace firm::hwtrade {

struct Beat { bool last; std::uint8_t keep; std::uint64_t data; };
struct Order { long cycle; std::uint32_t id, qty, price; };

class Model {
public:
    Model(std::uint16_t loc, std::uint16_t burst, std::uint16_t refill)
        : loc_(loc), burst_(burst), refill_(refill), tokens_(burst) {}

    // One clock edge: `beat` is the input of this cycle (empty for an idle cycle).
    void step(long cycle, const std::optional<Beat>& beat, std::uint32_t thresh, std::uint32_t max_qty,
              bool kill) {
        bool n_trig = false;
        std::uint32_t n_qty = 0, n_price = 0;
        if (beat) parse(*beat, thresh, n_trig, n_qty, n_price);
        if (passed_ && !kill) orders.push_back({cycle, next_id_++, pqty_, pprice_});   // stage 3
        const bool refill_now = since_ + 1 == refill_;                                     // stage 2
        std::uint16_t new_tokens = (refill_now && tokens_ < burst_) ? tokens_ + 1 : tokens_;
        since_ = refill_now ? 0 : since_ + 1;
        bool new_pass = false;
        if (trig_) {
            if (kill || tqty_ > max_qty || tokens_ == 0) {
                ++rejects;
            } else {
                new_pass = true, pqty_ = tqty_, pprice_ = tprice_;
                new_tokens = tokens_ - 1 + ((refill_now && tokens_ < burst_) ? 1 : 0);
            }
        }
        tokens_ = new_tokens, passed_ = new_pass;
        trig_ = n_trig, tqty_ = n_qty, tprice_ = n_price;                                   // stage 1
    }

    std::vector<Order> orders;
    std::uint32_t rejects = 0;

private:
    void parse(const Beat& b, std::uint32_t thresh, bool& trig, std::uint32_t& qty, std::uint32_t& price) {
        for (int i = 0; i < 8; ++i) {
            if (!((b.keep >> (7 - i)) & 1)) continue;
            const std::uint8_t x = static_cast<std::uint8_t>(b.data >> (56 - 8 * i));
            if (ls_ == 0) {
                if (pp_ == 19) ls_ = 1;
            } else if (ls_ == 1) {
                ml_ = static_cast<std::uint16_t>((x << 8) | (ml_ & 0xFF)), ls_ = 2;
            } else if (ls_ == 2) {
                ml_ = static_cast<std::uint16_t>((ml_ & 0xFF00) | x), mp_ = 0, ls_ = 3;
            } else {
                if (mp_ == 0) mt_ = x;
                if (mp_ == 1) mc_ = static_cast<std::uint16_t>((x << 8) | (mc_ & 0xFF));
                if (mp_ == 2) mc_ = static_cast<std::uint16_t>((mc_ & 0xFF00) | x);
                if (mp_ == 19) ms_ = x;
                if (mp_ >= 20 && mp_ <= 23) mq_ = (mq_ << 8) | x;
                if (mp_ >= 32 && mp_ <= 35) mr_ = (mr_ << 8) | x;
                if (mp_ + 1 == ml_) {
                    if (mt_ == 'A' && ml_ == 36 && mc_ == loc_ && ms_ == 'S' && mr_ <= thresh)
                        trig = true, qty = mq_, price = mr_;
                    ls_ = 1;
                }
                ++mp_;
            }
            ++pp_;
        }
        if (b.last) pp_ = 0, ls_ = 0;
    }

    std::uint16_t loc_, burst_, refill_;
    std::uint16_t pp_ = 0, ml_ = 0, mp_ = 0, mc_ = 0, tokens_, since_ = 0;
    std::uint8_t ls_ = 0, mt_ = 0, ms_ = 0;
    std::uint32_t mq_ = 0, mr_ = 0, tqty_ = 0, tprice_ = 0, pqty_ = 0, pprice_ = 0, next_id_ = 1;
    bool trig_ = false, passed_ = false;
};

}  // namespace firm::hwtrade
