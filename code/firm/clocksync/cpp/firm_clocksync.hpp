// firm.clocksync (C++20): the PI clock servo of One Quant Book 14, chapter 4 (Python reference: firm_clocksync.py).
// Given a measured offset (ns) every interval (s), step the phase by kp * offset and integrate ki * offset / interval
// into the frequency correction (ppb). Same operations, same order as the reference.
#pragma once

namespace firm::clocksync {

struct Servo {
    double kp = 0.7, ki = 0.3, freq_ppb = 0.0;
    // returns the phase step (ns); freq_ppb holds the frequency correction after the update
    double update(double offset_ns, double interval_s) {
        freq_ppb += ki * offset_ns / interval_s;
        return kp * offset_ns;
    }
};

}  // namespace firm::clocksync
