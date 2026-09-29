# 2. Capturing and Storing Tick Data — brief and source ledger

## Brief

- **Hook.** The consolidated US options feed carries billions of messages on a busy day; a firm that keeps every one of them for years is running a storage business on the side, and the first decision is what exactly to keep: the packets as they arrived, or the events they meant.
- **Sections.** What tick data is, and where it is captured; Raw capture against normalised storage; Record layouts and encodings; Partitioning and compression; Retention, tiers and the economics of petabytes.
- **Defines.** tick data, raw capture, partitioning, partition key, compression ratio, storage tier, retention policy.
- **Uses (defined earlier).** market data feed (B1.4), sequence number (B1.28), exchange timestamp (B1.28), receive timestamp (B1.28), normalisation (B1.28), market-by-order (B1.19), packet capture (B14.5), redundant feed lines (B10.26), line arbitration (B13.16), message gap (B13.16), feed handler (B13.18), input journal (B13.23).
- **Tutorial.** Generate a busy simulated hour with firm.exchsim's recorded-day script (two instruments, lines A and B), keep the raw capture (send time, length, MoldUDP64 packet), normalise it into fixed-width event records with the simulator's codec, and measure bytes per message raw, normalised, and compressed with zlib, zstd-in-Parquet and delta-plus-zlib; then partition by date and instrument and compare the bytes a one-instrument query must read. End state: a table of bytes per message by layout and a chart of compression ratio against compression speed.
- **Build.** `firm.tickcap`: capture writer (append-only raw files with an index), normaliser from raw packets to event records (arbitrating lines A and B, recording gaps), partitioned layout, compression study and a storage-cost calculator (bytes a day, tiers, retention) driven by cited message rates and prices; Python.
- **Weekend problem.** A petabyte a year? -- named result: the storage a firm needs for five years of full-depth US options and equities capture, raw and normalised, from cited message counts and the measured bytes per message and compression ratios, and its annual cost by tier.
- **Facts to verify.** OPRA or the options industry's published peak and average daily message counts (dated); US equities SIP or exchange daily message statistics (dated); a cloud object-storage price list: standard, infrequent and archive tiers per GB-month (dated); zstd and zlib reference documentation (compression levels); SEC Rule 17a-4 / CAT record retention periods (dated).
- **Data.** firm.exchsim make_recorded_day.py at reduced size (tests) and one busy hour generated once, late, under nice; nothing committed but the script and small fixtures.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | OPRA capacity projections (notice to multicast data subscribers, 15 September 2025): effective 7/2026, maximum output 13.575 million messages per 100 ms, total 311 billion messages per day; projections are for one of two redundant streams | Options Price Reporting Authority / SIAC, "Revised OPRA Capacity Projections" | https://cdn.opraplan.com/documents/notices/OPRA_Capacity_Projections_Update_0925.pdf | 2026-09-28 | table row "7/2026 13.575 4.403 1564 1.562 0.501 169 311 625"; "the traffic projections are for one stream only. For fault tolerance purposes, two redundant streams of data are available" | dat:pl:capturing-and-storing-tick-data:numbers; hook; section 5 |
| F2 | Amazon S3 storage prices, US East (N. Virginia): S3 Standard first 50 TB USD 0.023 per GB-month; Standard-Infrequent Access 0.0125; Glacier Flexible Retrieval 0.004; Glacier Deep Archive 0.00099 | Amazon Web Services, Amazon S3 pricing page | https://aws.amazon.com/s3/pricing/ | 2026-09-28 | "S3 Standard (first 50 TB): $0.023"; "S3 Standard-Infrequent Access: $0.0125"; "S3 Glacier Deep Archive: $0.00099" | dat:pl:capturing-and-storing-tick-data:numbers; section 5 table |
| F3 | RTS 6, article 28(3): records of orders kept for five years from the submission of an order | Commission Delegated Regulation (EU) 2017/589, Publications Office of the EU (CELEX 32017R0589) | http://publications.europa.eu/resource/celex/32017R0589 | 2026-09-28 | "The records referred to in paragraphs 1 and 2 shall be kept for five years from the date of the submission of an order to a trading venue or to another investment firm for execution." | dat:pl:capturing-and-storing-tick-data:retention |
| F4 | RFC 8878, Zstandard Compression and the 'application/zstd' Media Type, Informational, February 2021 (Collet; Kucherawy, ed.) | RFC Editor | https://www.rfc-editor.org/rfc/rfc8878.txt | 2026-09-28 | header: "Request for Comments: 8878", "February 2021", title | omsources |
| F5 | RFC 1950, ZLIB Compressed Data Format Specification version 3.3, May 1996 (Deutsch, Gailly) | RFC Editor | https://www.rfc-editor.org/rfc/rfc1950.txt | 2026-09-28 | header: "Request for Comments: 1950", "May 1996", Gailly | omsources |

## EXCLUDED

- US equities SIP daily message statistics (brief): not needed; the options feed's planned capacity is the example.
- SEC Rule 17a-4 / CAT retention (brief): the EU rule is the example in the dated box; US order records are Book 1's and Book 11's.

