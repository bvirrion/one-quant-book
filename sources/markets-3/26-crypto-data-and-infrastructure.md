# 26. Crypto Data and Infrastructure — brief and source ledger

## Brief

- **Hook.** A purchased order-book history shows a crossed book for two seconds on a quiet afternoon: one websocket update was lost, and nothing downstream noticed.
- **Sections.** Running nodes; On-chain data: logs and indexers; Venue market data: snapshots, deltas and checksums; Timestamps and what they mean; Where the matching engines sit.
- **Defines.** full node, archive node, RPC endpoint, event log, indexer, snapshot-and-delta feed, book checksum, cloud region.
- **Uses (defined earlier).** sequence number, market data feed, market-by-price, exchange timestamp, receive timestamp, normalisation, level 2, mempool, rate limit, smart contract, blockchain.
- **Tutorial.** Rebuild an order book from a snapshot and a stream of update-id-numbered deltas, detect gaps, resynchronise, and verify the book against a CRC32 checksum.
- **Build.** `firm.wsbook`: websocket book builder with gap detection, resync and checksum (C++20, Rust, Python reference); feeds `firm.triarb`.
- **Weekend problem.** The missing delta — named result: the fraction of time a book is wrong for a stated message-loss rate without checksums and with resynchronisation, and the expected duration of an error.
- **Facts to verify.** Ethereum full and archive node disk sizes (client docs, dated); Binance depth-stream update-id rules (Binance docs); OKX order-book checksum (OKX docs); historical data vendors' dataset descriptions (vendor docs); publicly stated hosting region of at least one major venue (venue or provider statement).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Ethereum full nodes keep recent state (typically last 128 blocks); archive nodes keep everything, units of terabytes; Erigon full archive sync around 2TB in under 3 days; execution clients Geth, Nethermind, Besu, Erigon, Reth | ethereum.org, "Nodes and clients" (GitHub ethereum/ethereum-org-website) | https://raw.githubusercontent.com/ethereum/ethereum-org-website/dev/public/content/developers/docs/nodes-and-clients/index.md | 2026-09-24 | "full nodes only keep a local copy of relatively recent data (typically the most recent 128 blocks)"; "around 2TB of disk space, in under 3 days" | dat:m3:crypto-data-and-infrastructure:nodes |
| F2 | Binance local order book procedure: buffer, snapshot lastUpdateId, discard u <= lastUpdateId, ignore u < book id, restart if U > id + 1, quantity zero removes, set id to u; connection valid 24 hours; ping every 20 seconds | Binance spot API docs, web-socket-streams.md (GitHub binance/binance-spot-api-docs) | https://raw.githubusercontent.com/binance/binance-spot-api-docs/master/web-socket-streams.md | 2026-09-24 | "If the event first update ID (U) is greater than the update ID of your local order book + 1, you have missed some events" | dat:m3:crypto-data-and-infrastructure:binance; firm.wsbook |
| F3 | Kraken WebSocket v2 book checksum: top 10 levels; asks low to high then bids high to low; remove decimal point and leading zeros from price and quantity; concatenate; CRC32 as unsigned 32-bit; verification optional | Kraken API docs, spot WS book v2 guide | https://docs.kraken.com/api/docs/guides/spot-ws-book-v2 | 2026-09-24 | "The checksum is always calculated over the top 10 price levels regardless of subscription depth" | dat:m3:crypto-data-and-infrastructure:kraken; firm.wsbook |
| F4 | Tardis.dev datasets: timestamp provided by exchange in microseconds (local_timestamp fallback), local_timestamp is message arrival time; incremental_book_L2 from real-time websocket feeds; files may contain updates before the first snapshot, to be skipped | Tardis.dev docs, downloadable CSV data types | https://docs.tardis.dev/downloadable-csv-files/data-types.md | 2026-09-24 | "local_timestamp: message arrival timestamp in microseconds since epoch" | dat:m3:crypto-data-and-infrastructure:tardis |
| F5 | Binance API endpoint api-gcp.binance.com | see chapter 25 ledger F3 | https://developers.binance.com/docs/binance-spot-api-docs/rest-api/general-api-information | 2026-09-24 | "https://api-gcp.binance.com" | §5 |
| F6 | OKX, 23 Jun 2026: checksum field deprecated in order book channels books, books-l2-tbt, books50-l2-tbt; still present but fixed to 0; use seqId/prevSeqId to verify continuity | OKX API v5 change log | https://www.okx.com/docs-v5/log_en/ | 2026-09-24 | "The checksum field is still present in snapshot and incremental updates, but its value is fixed to 0 and must no longer be used for integrity verification. Please use seqId/prevSeqId to verify the data continuity and accuracy." | dat:m3:crypto-data-and-infrastructure:kraken |
| F7 | Hyperliquid's 24 validators clustered in AWS Tokyo (ap-northeast-1) across multiple availability zones; Tokyo users reach them in 2-3 ms, European users face delays exceeding 200 ms (Glassnode research) | CoinDesk, 30 Mar 2026 | https://www.coindesk.com/markets/2026/03/30/hyperliquid-traders-in-tokyo-get-200-millisecond-edge-glassnode-research-shows | 2026-09-24 | "Hyperliquid's 24 validators are clustered in Tokyo, deployed across multiple availability zones in Amazon Web Services' ap-northeast-1 region"; "as little as 2 to 3 milliseconds"; "delays exceeding 200 milliseconds" | dat:m3:crypto-data-and-infrastructure:region |

## EXCLUDED

- The hosting region of a major venue (a venue or provider statement): none fetched; the text says only that some venues run in public clouds, citing one venue's cloud-named endpoint. **restored → F7 (a research firm's measurement reported by CoinDesk; no venue statement found, re-searched 2026-09-24).**
- OKX's order-book checksum documentation: not fetched; Kraken's is used. **restored → F6 (OKX has since deprecated the checksum; stated as such).**
- The message-loss model (20 levels, independent losses, 50-message resync) is illustrative. **illustrative by design, not a sourcing gap.**
