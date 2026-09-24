# 28. Reading Market Data — brief and source ledger

## Brief

- **Hook.** Forty million messages before lunch, and one of them is wrong.
- **Sections.** Levels of data; Trades, quotes and condition codes; Timestamps; Symbology and reference data; From raw feed to research table.
- **Defines.** level 1, level 2, level 3, trade condition, exchange timestamp, receive timestamp, sequence number, symbology, reference data, normalisation.
- **Tutorial.** Parse a binary order-by-order feed sample into a book and a trades table.
- **Build.** `firm.feed`: feed normaliser (C++/Rust decoder, Python reader).
- **Weekend problem.** The bad tick — named result: the number of trades to exclude and the corrected VWAP.
- **Facts to verify.** Nasdaq ITCH 5.0 message spec; CTA/UTP sale condition codes; MiFID II RTS 25 clock sync; CAT clock sync.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | TotalView-ITCH 5.0: all integer fields big-endian; Price(4) with four implied decimals; timestamps nanoseconds since midnight (6 bytes); stock locate at the same position in all messages; Add Order (A): offsets type 0, locate 1, tracking 3, timestamp 5, order reference 11 (8), buy/sell 19, shares 20 (4), stock 24 (8), price 32 (4) = 36 bytes; Order Executed (E): reference 11, executed shares 19 (4), match number 23 (8) = 31 bytes; Order Cancel (X) = 23 bytes; Order Delete (D) = 19 bytes; spec revision dated 28 April 2023 | Nasdaq TotalView-ITCH 5.0 specification (pdftotext) | https://www.nasdaqtrader.com/content/technicalsupport/specifications/dataproducts/NQTVITCHspecification.pdf | 2026-09-18 | "All integer fields are big endian (network byte order)"; message tables | dat:m1:reading-market-data:itch; build wire format |
| F2 | MiFID II RTS 25: members using a high-frequency algorithmic trading technique: maximum divergence from UTC 100 microseconds, timestamp granularity 1 microsecond or better | Commission Delegated Regulation (EU) 2017/574, as summarised by vendors (search excerpts) | https://www.online-ntp-validator.com/mifid-ii-clock-synchronization-rts-25.html | 2026-09-18 | "a maximum divergence from UTC of 100 microseconds, with timestamp granularity of 1 microsecond or better" | dat:m1:reading-market-data:clocks; exo 5 |
| F3 | CAT NMS Plan: participants (exchanges) within 100 microseconds of NIST; industry members within 50 milliseconds; one second for manual-event clocks | CAT NMS Plan FAQ R1 (search excerpt); FINRA Rule 6820 | https://www.catnmsplan.com/faq/r1 | 2026-09-18 | quoted excerpt | dat clocks |

## EXCLUDED

- CTA/UTP sale condition letters and the tables of which conditions update last/high/low/volume: not fetched; the chapter defines condition categories in words and the problem uses "this book's labels".
- FINRA's ten-second reporting requirement for off-exchange trades: not verified in this run; the text says "seconds late".
- The two-byte length framing: a property of common file distributions of ITCH data, not of the specification; declared as the build's own framing.
- Message volumes ("tens of millions before lunch"): unquantified on purpose; OPRA's verified figures are in chapter 24.
- The P message of the build has the layout of the specification's non-cross Trade message as recalled (44 bytes); it was NOT checked field by field against the PDF and is described only as part of the teaching subset.
