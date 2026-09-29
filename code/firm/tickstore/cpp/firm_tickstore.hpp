// firm::tickstore -- read the tick store's flat files in place, through a memory map (One Quant Book 15, ch. 4).
// A file is a header (magic "OQTS", u16 version, u16 record size, u32 schema length, the schema as JSON, padding
// to 64 bytes) followed by fixed-width little-endian records: version 1 is the 56-byte event of firm.tickcap
// (receive time and Book 13's feed event), version 2 appends venue u16, flags u16 and 4 bytes of padding (64).
#pragma once

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <fcntl.h>
#include <map>
#include <stdexcept>
#include <string>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>

namespace firm::tickstore {

struct Event {                       // the fields every version has, at the same offsets
    std::uint64_t recv, seq, ts, ref, ref2, qty;
    std::uint32_t price;
    std::uint16_t locate;
    std::uint8_t kind, side;
};

template <class T> T load(const std::uint8_t* p) { T v; std::memcpy(&v, p, sizeof v); return v; }

class FlatFile {
public:
    explicit FlatFile(const std::string& path) {
        fd_ = ::open(path.c_str(), O_RDONLY);
        if (fd_ < 0) throw std::runtime_error("cannot open " + path);
        struct stat st {};
        ::fstat(fd_, &st);
        size_ = static_cast<std::size_t>(st.st_size);
        void* m = ::mmap(nullptr, size_, PROT_READ, MAP_PRIVATE, fd_, 0);
        if (m == MAP_FAILED) throw std::runtime_error("mmap failed");
        base_ = static_cast<const std::uint8_t*>(m);
        if (size_ < 12 || std::memcmp(base_, "OQTS", 4) != 0)
            throw std::runtime_error("not a flat file");
        version_ = load<std::uint16_t>(base_ + 4);
        record_ = load<std::uint16_t>(base_ + 6);
        std::size_t start = 12 + load<std::uint32_t>(base_ + 8);
        start_ = (start + 63) / 64 * 64;
        bool known = (version_ == 1 && record_ == 56) || (version_ == 2 && record_ == 64);
        if (!known) throw std::runtime_error("unknown version");
        n_ = (size_ - start_) / record_;
    }
    FlatFile(const FlatFile&) = delete;
    FlatFile& operator=(const FlatFile&) = delete;
    ~FlatFile() { ::munmap(const_cast<std::uint8_t*>(base_), size_); ::close(fd_); }

    std::size_t size() const { return n_; }
    int version() const { return version_; }
    Event operator[](std::size_t i) const {   // pages are read from disk when first touched
        const std::uint8_t* p = base_ + start_ + i * record_;
        using U64 = std::uint64_t;
        return {load<U64>(p), load<U64>(p + 12), load<U64>(p + 20), load<U64>(p + 28),
                load<U64>(p + 36), load<U64>(p + 48), load<std::uint32_t>(p + 44),
                load<std::uint16_t>(p + 10), p[8], p[9]};
    }

private:
    int fd_ = -1;
    const std::uint8_t* base_ = nullptr;
    std::size_t size_ = 0, start_ = 0, n_ = 0;
    int version_ = 0, record_ = 0;
};

struct Summary { std::uint64_t count = 0, executed = 0, last_seq = 0; };

// Per instrument: records, quantity executed (kind 'E'), last sequence number.
inline std::map<std::uint16_t, Summary> summarise(const FlatFile& f) {
    std::map<std::uint16_t, Summary> out;
    for (std::size_t i = 0; i < f.size(); ++i) {
        const Event e = f[i];
        Summary& s = out[e.locate];
        ++s.count;
        if (e.kind == 'E') s.executed += e.qty;
        if (e.seq > s.last_seq) s.last_seq = e.seq;
    }
    return out;
}

}  // namespace firm::tickstore
