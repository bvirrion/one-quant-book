#pragma once
#include <condition_variable>
#include <cstddef>
#include <deque>
#include <mutex>
#include <optional>
#include <utility>

template <class T>
class BoundedQueue {
    std::mutex m_;
    std::condition_variable not_empty_, not_full_;
    std::deque<T> q_;
    const std::size_t cap_;
    bool closed_ = false;

public:
    explicit BoundedQueue(std::size_t cap) : cap_(cap) {}

    bool push(T x) {
        std::unique_lock lock(m_);
        not_full_.wait(lock, [&] { return q_.size() < cap_ || closed_; });
        if (closed_) return false;
        q_.push_back(std::move(x));
        lock.unlock();
        not_empty_.notify_one();
        return true;
    }
    std::optional<T> pop() {
        std::unique_lock lock(m_);
        not_empty_.wait(lock, [&] { return !q_.empty() || closed_; });
        if (q_.empty()) return std::nullopt;     // closed and drained
        T x = std::move(q_.front());
        q_.pop_front();
        lock.unlock();
        not_full_.notify_one();
        return x;
    }
    void close() {
        { std::lock_guard lock(m_); closed_ = true; }
        not_empty_.notify_all();
        not_full_.notify_all();
    }
};
