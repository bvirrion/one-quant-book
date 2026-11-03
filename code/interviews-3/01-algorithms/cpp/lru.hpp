#pragma once
#include <cstddef>
#include <list>
#include <optional>
#include <unordered_map>
#include <utility>

template <class K, class V>
class Lru {
public:
    explicit Lru(std::size_t capacity) : capacity_(capacity) {}

    std::optional<V> get(const K& key) {
        auto it = where_.find(key);
        if (it == where_.end()) return std::nullopt;
        items_.splice(items_.begin(), items_, it->second);  // relinks: iterators stay valid
        return it->second->second;
    }

    void put(const K& key, V value) {
        if (capacity_ == 0) return;
        if (auto it = where_.find(key); it != where_.end()) {
            it->second->second = std::move(value);
            items_.splice(items_.begin(), items_, it->second);
            return;
        }
        if (items_.size() == capacity_) {
            where_.erase(items_.back().first);
            items_.pop_back();
        }
        items_.emplace_front(key, std::move(value));
        where_[key] = items_.begin();
    }

private:
    std::size_t capacity_;
    std::list<std::pair<K, V>> items_;  // most recently used at the front
    std::unordered_map<K, typename std::list<std::pair<K, V>>::iterator> where_;
};
