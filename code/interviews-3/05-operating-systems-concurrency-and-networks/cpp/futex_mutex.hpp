#pragma once
#include <atomic>
#include <linux/futex.h>
#include <sys/syscall.h>
#include <unistd.h>

class FutexMutex {
    std::atomic<int> state_{0};             // 0 free, 1 locked, 2 locked and maybe waiters

    long futex(int op, int value) {
        auto* word = reinterpret_cast<int*>(&state_);
        return syscall(SYS_futex, word, op, value, nullptr, nullptr, 0);
    }

public:
    static inline std::atomic<long> waits{0}, wakes{0};

    void lock() {
        int c = 0;
        if (state_.compare_exchange_strong(c, 1, std::memory_order_acquire)) return;
        if (c != 2) c = state_.exchange(2, std::memory_order_acquire);
        while (c != 0) {
            ++waits;
            futex(FUTEX_WAIT_PRIVATE, 2);        // sleeps only if the state is still 2
            c = state_.exchange(2, std::memory_order_acquire);
        }
    }
    void unlock() {
        if (state_.exchange(0, std::memory_order_release) == 2) {
            ++wakes;
            futex(FUTEX_WAKE_PRIVATE, 1);
        }
    }
};
