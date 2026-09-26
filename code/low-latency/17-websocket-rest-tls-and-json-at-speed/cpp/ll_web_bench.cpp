// Chapter 17 benchmark: the CPU costs of one websocket order, component by component.
//   frame    decode (unmask and parse) a masked 300-byte text frame, and encode one
//   depth    decode the fixture's depth updates: structural index against a tree-building parser
//   sign     HMAC-SHA-256 of a 119-byte request: the build's portable signer with its pads precomputed and with the key
//            hashed every time; OpenSSL's HMAC() (key every time) and OpenSSL with the pads precomputed
//   aead     AES-128-GCM seal and open of a 300-byte record (what a TLS 1.3 record costs each way), with OpenSSL
// Output: key,ns
#include <openssl/evp.h>
#include <openssl/hmac.h>

#include <cstdio>
#include <fstream>
#include <string>
#include <vector>

#include "firm_ubench.hpp"
#include "firm_wsclient.hpp"
#include "ll_json_naive.hpp"

using namespace firm::ubench;

template <class F>
static double per(const Clock& clk, std::size_t n, F&& f, int reps = 21) {
    std::vector<double> t;
    for (int r = 0; r < reps + 2; ++r) {
        const std::uint64_t a = tsc_start();
        for (std::size_t i = 0; i < n; ++i) f(i);
        const std::uint64_t b = rdtscp();
        if (r >= 2) t.push_back(clk.ns(b - a) / static_cast<double>(n));
    }
    return quantile(t, 0.5);
}

int main() {
    const Clock clk = Clock::calibrate();
    std::uint64_t sink = 0;

    // frames
    std::string msg(300, 'x');
    const std::uint8_t key[4] = {1, 2, 3, 4};
    std::uint8_t wire[400], work[400];
    const std::size_t fl = firm::ws::encode_frame(wire, reinterpret_cast<const std::uint8_t*>(msg.data()), msg.size(),
                                                  firm::ws::kText, true, key);
    const double fdec = per(clk, 1000, [&](std::size_t) {
        std::memcpy(work, wire, fl);
        firm::ws::FrameView f;
        firm::ws::FrameError e;
        sink += firm::ws::decode_frame(work, fl, f, e) + f.payload[7];
    });
    const double fcopy = per(clk, 1000, [&](std::size_t) { std::memcpy(work, wire, fl); sink += work[9]; });
    const double fenc = per(clk, 1000, [&](std::size_t) {
        sink += firm::ws::encode_frame(work, reinterpret_cast<const std::uint8_t*>(msg.data()), msg.size(), firm::ws::kText,
                                       true, key);
    });

    // depth updates
    std::ifstream in("code/firm/wsclient/data/depth_updates.jsonl");
    std::vector<std::string> ups;
    std::size_t bytes = 0;
    for (std::string l; std::getline(in, l);) { bytes += l.size(); ups.push_back(l); }
    const double idx = per(clk, ups.size(), [&](std::size_t i) {
        firm::ws::Depth d;
        firm::ws::decode_depth(ups[i], d);
        sink += d.nb + static_cast<std::uint64_t>(d.bids[0].price);
    });
    const double naive = per(clk, ups.size(), [&](std::size_t i) {
        const auto d = ll::naive::decode_depth(ups[i]);
        sink += d.bids.size() + d.last;
    }, 7);

    // signing
    const std::string secret = "NhqPtmdSJYdKjVHjA7PZj4Mge3R5YNiP1e3UZjInClVN65XAbvqqM6A7H5fATj0j";
    const std::string payload = "symbol=BTCUSDT&side=BUY&type=LIMIT&timeInForce=GTC&quantity=0.01&price=64123.25&recvWindow=5000&timestamp=1758800000123";
    const firm::ws::HmacSha256 pre(secret);
    std::uint8_t out[32];
    const double sign_pre = per(clk, 1000, [&](std::size_t) { pre.sign(payload, out); sink += out[3]; });
    const double sign_key = per(clk, 1000, [&](std::size_t) { firm::ws::HmacSha256(secret).sign(payload, out); sink += out[3]; });
    unsigned int olen = 0;
    const double sign_ossl = per(clk, 1000, [&](std::size_t) {
        HMAC(EVP_sha256(), secret.data(), static_cast<int>(secret.size()), reinterpret_cast<const unsigned char*>(payload.data()),
             payload.size(), out, &olen);
        sink += out[3];
    });

    // AEAD: a TLS 1.3 record's protection, AES-128-GCM
    unsigned char k[16] = {7}, iv[12] = {9}, tag[16], ct[400], pt[400];
    EVP_CIPHER_CTX* ctx = EVP_CIPHER_CTX_new();
    int len = 0;
    // the key schedule once per connection, as TLS does; each record only sets its nonce
    EVP_CIPHER_CTX* dctx = EVP_CIPHER_CTX_new();
    EVP_EncryptInit_ex(ctx, EVP_aes_128_gcm(), nullptr, k, iv);
    EVP_DecryptInit_ex(dctx, EVP_aes_128_gcm(), nullptr, k, iv);
    const double seal = per(clk, 1000, [&](std::size_t) {
        EVP_EncryptInit_ex(ctx, nullptr, nullptr, nullptr, iv);
        EVP_EncryptUpdate(ctx, ct, &len, reinterpret_cast<const unsigned char*>(msg.data()), static_cast<int>(msg.size()));
        EVP_EncryptFinal_ex(ctx, ct + len, &len);
        EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_GET_TAG, 16, tag);
        sink += tag[0];
    });
    const double open = per(clk, 1000, [&](std::size_t) {
        EVP_DecryptInit_ex(dctx, nullptr, nullptr, nullptr, iv);
        EVP_DecryptUpdate(dctx, pt, &len, ct, 300);
        EVP_CIPHER_CTX_ctrl(dctx, EVP_CTRL_GCM_SET_TAG, 16, tag);
        sink += static_cast<std::uint64_t>(EVP_DecryptFinal_ex(dctx, pt + len, &len)) + pt[5];
    });
    EVP_CIPHER_CTX_free(ctx);
    EVP_CIPHER_CTX_free(dctx);
    // OpenSSL with the pads precomputed: a keyed context copied for each signature (RFC 2104's precomputation with
    // the library's SHA-256, which uses the processor's SHA instructions where they exist)
    HMAC_CTX* base = HMAC_CTX_new();
    HMAC_CTX* hw = HMAC_CTX_new();
    HMAC_Init_ex(base, secret.data(), static_cast<int>(secret.size()), EVP_sha256(), nullptr);
    const double sign_ossl_pre = per(clk, 1000, [&](std::size_t) {
        HMAC_CTX_copy(hw, base);
        HMAC_Update(hw, reinterpret_cast<const unsigned char*>(payload.data()), payload.size());
        HMAC_Final(hw, out, &olen);
        sink += out[3];
    });
    HMAC_CTX_free(base);
    HMAC_CTX_free(hw);
    do_not_optimize(sink);
    std::printf("key,ns\nframe_decode,%.1f\nframe_copy,%.1f\nframe_encode,%.1f\ndepth_index,%.1f\ndepth_naive,%.1f\n"
                "sign_precomputed,%.1f\nsign_rekey,%.1f\nsign_openssl,%.1f\nsign_openssl_pre,%.1f\naead_seal,%.1f\n"
                "aead_open,%.1f\n",
                fdec, fcopy, fenc, idx, naive, sign_pre, sign_key, sign_ossl, sign_ossl_pre, seal, open);
    std::fprintf(stderr, "%zu updates, %.0f bytes each\n", ups.size(), static_cast<double>(bytes) / static_cast<double>(ups.size()));
    return 0;
}
