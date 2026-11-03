#pragma once
#include <cstddef>
#include <new>
#include <utility>

template <class T, std::size_t N>
class Pool {
    union Slot {
        Slot* next;
        alignas(T) unsigned char bytes[sizeof(T)];
    };
    Slot slots_[N];
    Slot* free_ = slots_;

public:
    Pool() {
        for (std::size_t i = 0; i + 1 < N; ++i) slots_[i].next = &slots_[i + 1];
        slots_[N - 1].next = nullptr;
    }
    Pool(const Pool&) = delete;
    Pool& operator=(const Pool&) = delete;

    template <class... A>
    T* create(A&&... a) {
        if (!free_) return nullptr;
        Slot* s = free_;
        free_ = s->next;                         // read now: the object overwrites it
        try {
            return ::new (static_cast<void*>(s->bytes)) T(std::forward<A>(a)...);
        } catch (...) {
            s->next = free_;                     // a failed constructor loses no slot
            free_ = s;
            throw;
        }
    }
    void destroy(T* p) noexcept {
        p->~T();
        Slot* s = reinterpret_cast<Slot*>(p);
        s->next = free_;
        free_ = s;
    }
};
