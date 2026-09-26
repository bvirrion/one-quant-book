// firm.ring -- rings and a sequence lock over raw memory (build of One Quant Book 13, chapter 12), C++20, header only.
// The same byte layout is used in one process, between processes over shared memory, and by the Rust twin:
//
//   offset   0  header line : magic u64 | version u32 | slot_size u32 | capacity u64   (little-endian)
//   offset  64  write line  : u64 sequence of the next slot the producer will write
//   offset 128  read line   : u64 sequence of the next slot the consumer will read (SPSC only)
//   offset 192  slots       : capacity x slot_size bytes; a slot is u32 length | payload (slot_size - 4 bytes)
//
//   Spsc       single producer, single consumer; wait-free; full and empty reported to the caller
//   Broadcast  single producer, many independent readers; the producer never waits; each slot carries its sequence
//              number so that a reader that has been lapped (a slow consumer) detects it and can resynchronise
//   SeqLock<T> last-value publication of a small trivially copyable T (top of book), readers retry on change
//   Segment    a POSIX shared-memory region (shm_open + mmap) holding one ring
#pragma once
#include <fcntl.h>
#include <sys/mman.h>
#include <unistd.h>

#include <atomic>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <stdexcept>
#include <string>
#include <type_traits>

namespace firm::ring {

inline constexpr std::uint64_t kMagic = 0x474e4952'4d524946ull;  // "FIRMRING"
inline constexpr std::uint32_t kVersion = 1;
inline constexpr std::size_t kHeader = 192;

struct Header {
    std::uint64_t magic;
    std::uint32_t version, slot_size;
    std::uint64_t capacity;
};

inline std::atomic<std::uint64_t>& word(std::uint8_t* base, std::size_t off) {
    return *reinterpret_cast<std::atomic<std::uint64_t>*>(base + off);
}
static_assert(sizeof(std::atomic<std::uint64_t>) == 8 && std::atomic<std::uint64_t>::is_always_lock_free);

inline std::size_t region_size(std::uint64_t capacity, std::uint32_t slot_size) { return kHeader + capacity * slot_size; }

// Format a region: header, zero sequences, zero slots.
inline void format(std::uint8_t* base, std::uint64_t capacity, std::uint32_t slot_size) {
    if (capacity == 0 || (capacity & (capacity - 1)) || slot_size < 8 || slot_size % 8) throw std::invalid_argument("bad ring geometry");
    std::memset(base, 0, region_size(capacity, slot_size));
    const Header h{kMagic, kVersion, slot_size, capacity};
    std::memcpy(base, &h, sizeof h);
}

inline Header check(const std::uint8_t* base) {
    Header h;
    std::memcpy(&h, base, sizeof h);
    if (h.magic != kMagic || h.version != kVersion) throw std::runtime_error("not a firm ring (magic or version)");
    return h;
}

class Spsc {
public:
    // The caches start from the region's current sequences (a consumer may attach to a ring already in use).
    explicit Spsc(std::uint8_t* base)
        : base_(base), h_(check(base)), mask_(h_.capacity - 1),
          read_cache_(word(base, 128).load(std::memory_order_acquire)), write_cache_(word(base, 64).load(std::memory_order_acquire)) {}

    bool try_write(const void* msg, std::uint32_t len) {  // producer thread only
        if (len > h_.slot_size - 4) return false;
        const std::uint64_t w = word(base_, 64).load(std::memory_order_relaxed);
        if (w - read_cache_ == h_.capacity) {  // looks full: refresh the cached read position once
            read_cache_ = word(base_, 128).load(std::memory_order_acquire);
            if (w - read_cache_ == h_.capacity) return false;
        }
        std::uint8_t* slot = base_ + kHeader + (w & mask_) * h_.slot_size;
        std::memcpy(slot, &len, 4);
        std::memcpy(slot + 4, msg, len);
        word(base_, 64).store(w + 1, std::memory_order_release);  // publish
        return true;
    }

    int try_read(void* out, std::uint32_t cap) {  // consumer thread only; length, or -1 when empty
        const std::uint64_t r = word(base_, 128).load(std::memory_order_relaxed);
        if (r == write_cache_) {
            write_cache_ = word(base_, 64).load(std::memory_order_acquire);
            if (r == write_cache_) return -1;
        }
        const std::uint8_t* slot = base_ + kHeader + (r & mask_) * h_.slot_size;
        std::uint32_t len;
        std::memcpy(&len, slot, 4);
        if (len > cap) len = cap;
        std::memcpy(out, slot + 4, len);
        word(base_, 128).store(r + 1, std::memory_order_release);  // hand the slot back
        return static_cast<int>(len);
    }

    std::uint64_t written() const { return word(base_, 64).load(std::memory_order_acquire); }

private:
    std::uint8_t* base_;
    Header h_;
    std::uint64_t mask_, read_cache_, write_cache_;
};

// Broadcast: slot = u64 sequence (odd while being written, 2 * (seq + 1) when holding message seq) | u32 len | payload.
class Broadcast {
public:
    explicit Broadcast(std::uint8_t* base) : base_(base), h_(check(base)), mask_(h_.capacity - 1) {}

    void write(const void* msg, std::uint32_t len) {  // never waits: slow readers are lapped
        const std::uint64_t w = word(base_, 64).load(std::memory_order_relaxed);
        std::uint8_t* slot = base_ + kHeader + (w & mask_) * h_.slot_size;
        auto& seq = word(slot, 0);
        seq.store(2 * w + 1, std::memory_order_relaxed);  // odd: being written
        std::atomic_thread_fence(std::memory_order_release);
        std::memcpy(slot + 8, &len, 4);
        std::memcpy(slot + 12, msg, len);
        seq.store(2 * (w + 1), std::memory_order_release);
        word(base_, 64).store(w + 1, std::memory_order_release);
    }

    enum class Read { Ok, Empty, Overrun };

    // A reader keeps its own position `pos`. Overrun: the slot now holds a later message (the reader was too slow).
    Read read(std::uint64_t& pos, void* out, std::uint32_t& len) const {
        const std::uint8_t* slot = base_ + kHeader + (pos & mask_) * h_.slot_size;
        auto& seq = word(const_cast<std::uint8_t*>(slot), 0);
        const std::uint64_t s1 = seq.load(std::memory_order_acquire);
        if (s1 < 2 * (pos + 1)) return Read::Empty;
        if (s1 != 2 * (pos + 1)) return Read::Overrun;
        std::memcpy(&len, slot + 8, 4);
        std::memcpy(out, slot + 12, len);
        std::atomic_thread_fence(std::memory_order_acquire);
        if (seq.load(std::memory_order_relaxed) != s1) return Read::Overrun;  // overwritten while we copied
        ++pos;
        return Read::Ok;
    }

    std::uint64_t head() const { return word(base_, 64).load(std::memory_order_acquire); }  // for resynchronisation

private:
    std::uint8_t* base_;
    Header h_;
    std::uint64_t mask_;
};

// SeqLock<T>: the value is stored as relaxed atomic words, so that a reader copying while the writer writes is not a
// data race; the even/odd sequence tells the reader whether its copy is consistent.
template <class T>
class SeqLock {
    static_assert(std::is_trivially_copyable_v<T> && sizeof(T) % 8 == 0);
    static constexpr std::size_t kWords = sizeof(T) / 8;

public:
    void store(const T& v) {  // single writer
        const std::uint64_t s = seq_.load(std::memory_order_relaxed);
        seq_.store(s + 1, std::memory_order_relaxed);
        std::atomic_thread_fence(std::memory_order_release);
        std::uint64_t w[kWords];
        std::memcpy(w, &v, sizeof v);
        for (std::size_t i = 0; i < kWords; ++i) words_[i].store(w[i], std::memory_order_relaxed);
        seq_.store(s + 2, std::memory_order_release);
    }

    T load(std::uint64_t* retries = nullptr) const {
        for (;;) {
            const std::uint64_t s1 = seq_.load(std::memory_order_acquire);
            if (s1 & 1) { if (retries) ++*retries; continue; }
            std::uint64_t w[kWords];
            for (std::size_t i = 0; i < kWords; ++i) w[i] = words_[i].load(std::memory_order_relaxed);
            std::atomic_thread_fence(std::memory_order_acquire);
            if (seq_.load(std::memory_order_relaxed) == s1) {
                T v;
                std::memcpy(&v, w, sizeof v);
                return v;
            }
            if (retries) ++*retries;
        }
    }

private:
    alignas(64) std::atomic<std::uint64_t> seq_{0};
    std::atomic<std::uint64_t> words_[kWords]{};
};

// A shared-memory region: create (and format) or attach by name; unlinked by the creator's destructor.
class Segment {
public:
    Segment(const std::string& name, std::size_t bytes, bool create) : name_(name), size_(bytes), owner_(create) {
        const int fd = shm_open(name.c_str(), create ? (O_CREAT | O_RDWR | O_TRUNC) : O_RDWR, 0600);
        if (fd < 0) throw std::runtime_error("shm_open " + name);
        if (create && ftruncate(fd, static_cast<off_t>(bytes)) != 0) { close(fd); throw std::runtime_error("ftruncate"); }
        void* p = mmap(nullptr, bytes, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
        close(fd);
        if (p == MAP_FAILED) throw std::runtime_error("mmap " + name);
        base_ = static_cast<std::uint8_t*>(p);
    }
    Segment(const Segment&) = delete;
    Segment& operator=(const Segment&) = delete;
    ~Segment() {
        munmap(base_, size_);
        if (owner_) shm_unlink(name_.c_str());
    }
    std::uint8_t* data() const { return base_; }

private:
    std::string name_;
    std::size_t size_;
    bool owner_;
    std::uint8_t* base_ = nullptr;
};

}  // namespace firm::ring
