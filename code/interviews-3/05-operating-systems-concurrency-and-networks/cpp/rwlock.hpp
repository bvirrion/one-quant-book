#pragma once
#include <condition_variable>
#include <mutex>

class RwLock {
    std::mutex m_;
    std::condition_variable readers_, writers_;
    int active_readers_ = 0, waiting_writers_ = 0;
    bool writing_ = false;

    bool may_read() const { return !writing_ && waiting_writers_ == 0; }

public:
    void lock_shared() {
        std::unique_lock l(m_);
        readers_.wait(l, [&] { return may_read(); });
        ++active_readers_;
    }
    bool try_lock_shared() {
        std::lock_guard l(m_);
        if (!may_read()) return false;
        ++active_readers_;
        return true;
    }
    void unlock_shared() {
        std::lock_guard l(m_);
        if (--active_readers_ == 0 && waiting_writers_ > 0) writers_.notify_one();
    }
    void lock() {
        std::unique_lock l(m_);
        ++waiting_writers_;
        writers_.wait(l, [&] { return !writing_ && active_readers_ == 0; });
        --waiting_writers_;
        writing_ = true;
    }
    void unlock() {
        std::lock_guard l(m_);
        writing_ = false;
        if (waiting_writers_ > 0) writers_.notify_one();
        else readers_.notify_all();
    }
};
