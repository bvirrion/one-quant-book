// firm.wsclient (C++20): RFC 6455 frame forms, the fixture stream reassembled as the Python reference does, every
// depth update of the fixture decoded to the reference's values, and HMAC-SHA-256 against RFC 4231 and a venue's
// published example.
#include "firm_wsclient.hpp"

#include <cstdio>
#include <fstream>
#include <iterator>
#include <string>
#include <vector>

using namespace firm::ws;

static int fails = 0;
#define CHECK(c) do { if (!(c)) { std::printf("FAIL line %d: %s\n", __LINE__, #c); ++fails; } } while (0)

static std::string hex(std::string_view s) {
    static constexpr char x[] = "0123456789abcdef";
    std::string o;
    for (const unsigned char c : s) { o += x[c >> 4]; o += x[c & 15]; }
    return o;
}

static std::string line(const Depth& d) {
    std::string s = std::to_string(d.event_time) + " " + d.symbol + " " + std::to_string(d.first) + " " +
                    std::to_string(d.last) + "|";
    for (std::size_t i = 0; i < d.nb; ++i) s += (i ? "," : "") + std::to_string(d.bids[i].price) + ":" + std::to_string(d.bids[i].qty);
    s += "|";
    for (std::size_t i = 0; i < d.na; ++i) s += (i ? "," : "") + std::to_string(d.asks[i].price) + ":" + std::to_string(d.asks[i].qty);
    return s;
}

int main() {
    // RFC 6455 section 5.7 examples
    std::uint8_t out[80000];
    const std::uint8_t hello[] = {'H', 'e', 'l', 'l', 'o'}, key[] = {0x37, 0xfa, 0x21, 0x3d};
    std::size_t n = encode_frame(out, hello, 5, kText);
    CHECK(hex(std::string_view(reinterpret_cast<char*>(out), n)) == "810548656c6c6f");
    n = encode_frame(out, hello, 5, kText, true, key);
    CHECK(hex(std::string_view(reinterpret_cast<char*>(out), n)) == "818537fa213d7f9f4d5158");
    FrameView f;
    FrameError e;
    CHECK(decode_frame(out, n, f, e) == 11 && f.masked && std::string_view(reinterpret_cast<char*>(f.payload), f.len) == "Hello");
    std::vector<std::uint8_t> big(65536, 'x');
    n = encode_frame(out, big.data(), big.size(), kBinary);
    CHECK(out[1] == 127 && out[7] == 1 && out[8] == 0 && out[9] == 0 && n == 65546);
    std::uint8_t bad[] = {0x81, 0x7e, 0x00, 0x05, 'h', 'e', 'l', 'l', 'o'};
    CHECK(decode_frame(bad, sizeof bad, f, e) == 0 && e == FrameError::length_encoding);

    // the fixture stream
    std::ifstream fs("code/firm/wsclient/data/frames.bin", std::ios::binary);
    std::vector<std::uint8_t> st{std::istreambuf_iterator<char>(fs), {}};
    std::ifstream fe("code/firm/wsclient/data/frames_expected.txt");
    std::vector<std::string> want;
    for (std::string l; std::getline(fe, l);) want.push_back(l);
    Reassembler r;
    std::size_t i = 0, k = 0;
    while (i < st.size()) {
        const std::size_t used = decode_frame(st.data() + i, st.size() - i, f, e);
        CHECK(used > 0);
        if (used == 0) break;
        std::uint8_t op;
        std::string_view msg;
        if (r.feed(f, op, msg)) {
            const std::string got = std::to_string(op) + " " + hex(msg);
            if (k >= want.size() || got != want[k]) { ++fails; std::printf("message %zu differs\n", k); }
            ++k;
        }
        i += used;
    }
    CHECK(k == want.size());

    // depth updates
    std::ifstream du("code/firm/wsclient/data/depth_updates.jsonl"), dx("code/firm/wsclient/data/depth_expected.txt");
    std::size_t nd = 0;
    for (std::string a, b; std::getline(du, a) && std::getline(dx, b); ++nd) {
        Depth d;
        if (!decode_depth(a, d) || line(d) != b) {
            if (fails++ < 3) std::printf("depth %zu:\n  got  %s\n  want %s\n", nd, line(d).c_str(), b.c_str());
        }
    }
    CHECK(nd == 1000);
    Depth d;
    CHECK(!decode_depth(R"({"e":"depthUpdate","s":"A\"B"})", d));   // an escape: not this decoder's shape

    // HMAC-SHA-256
    CHECK(HmacSha256(std::string(20, '\x0b')).hex("Hi There") == "b0344c61d8db38535ca8afceaf0bf12b881dc200c9833da726e9376c2e32cff7");
    CHECK(HmacSha256("Jefe").hex("what do ya want for nothing?") == "5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843");
    CHECK(HmacSha256(std::string(131, '\xaa')).hex("Test Using Larger Than Block-Size Key - Hash Key First") ==
          "60e431591ee0b67f0d8a26aacbf5b77f8e0bc6213728c5140546040f0ee37f54");
    const HmacSha256 venue("NhqPtmdSJYdKjVHjA7PZj4Mge3R5YNiP1e3UZjInClVN65XAbvqqM6A7H5fATj0j");
    const std::string payload = "symbol=LTCBTC&side=BUY&type=LIMIT&timeInForce=GTC&quantity=1&price=0.1&recvWindow=5000&timestamp=1499827319559";
    CHECK(venue.hex(payload) == "c8db56825ae71d6d79447849e617115f4a920fa2acdcab2b053c4b2838bd6b71");
    CHECK(venue.hex(payload) == venue.hex(payload));
    std::printf("%s: %zu messages reassembled, %zu depth updates decoded\n", fails ? "FAILED" : "ok", k, nd);
    return fails ? 1 : 0;
}
