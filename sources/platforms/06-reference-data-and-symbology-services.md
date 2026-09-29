# 6. Reference Data and Symbology Services — brief and source ledger

## Brief

- **Hook.** On a June morning in 2022 a large US company's shares began trading under a new ticker, and its old ticker was later given to a different fund: every system that joined on tickers attached one issuer's history to another's without an error message.
- **Sections.** What the reference-data service serves; Vendors, conflicts and the golden copy; Symbol resolution through time; Corporate actions as a service; Counterparties, accounts and the rest.
- **Defines.** reference-data service, golden copy, symbol resolution, corporate-action event, counterparty master, instrument lifecycle event.
- **Uses (defined earlier).** symbology (B1.28), reference data (B1.28), security master (B7.4), permanent identifier (B7.4), identifier mapping (B7.4), ticker change (B7.4), adjustment factor (B1.8), stock split (B1.8), ex-dividend date (B1.8), legal entity identifier (B2.28), restatement (B7.3), point-in-time data (B7.3), valid time (B7.3), knowledge time (B7.3), bitemporal data (B7.3), as-of join (B7.3).
- **Tutorial.** Feed two synthetic vendor files that disagree (a late split, a mistyped lot size, a reused ticker) into a reference-data service built on firm.secmaster, firm.pit and firm.corpactions; build the golden copy with precedence rules and a bitemporal history; resolve symbols as of a date and as known at a date; serve adjustment factors as known at each decision time; run a backtest on latest-known against point-in-time reference data. End state: the share of instrument-days on which the two disagree and the backtest's P&L difference.
- **Build.** `firm.refdata`: vendor ingest and comparison, golden-copy rules with provenance per field, bitemporal instrument and counterparty tables, symbol resolution (`resolve(symbol, valid, known)`), corporate-action event service with announced/confirmed/cancelled states and point-in-time adjustment factors, futures roll and expiry calendar via firm.contracts; Python.
- **Weekend problem.** The ticker that changed hands -- named result: the P&L error of a backtest that resolves tickers with today's mapping over a universe with planted ticker reuse and late corporate actions, and zero error with point-in-time resolution.
- **Facts to verify.** Meta Platforms ticker change from FB to META effective 9 June 2022 (company or exchange notice); reuse of a retired ticker by another security (exchange or issuer notice); ISO 6166 ISIN and ISO 17442 LEI (GLEIF) standards; OpenFIGI / FIGI identifier documentation; ISO 15022 / 20022 corporate-action event types (SWIFT or ISO documentation).
- **Data.** Synthetic vendor files and firm.synthmkt's security master; no licensed reference data.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Meta Platforms press release of 31 May 2022: Class A common stock to trade on Nasdaq under the ticker META prior to market open on 9 June 2022, replacing FB; CUSIP unchanged | Meta Platforms investor relations, press release | https://investor.atmeta.com/investor-news/press-release-details/2022/Meta-Platforms-Inc.-to-Change-Ticker-Symbol-to-META-on-June-9/default.aspx | 2026-09-28 | "Class A common stock will begin trading on NASDAQ under the ticker symbol 'META' prior to market open on June 9, 2022. This will replace the company's current ticker symbol 'FB'"; the CUSIP number continues unchanged | hook; dat:pl:reference-data-and-symbology-services:meta; exercise 2 |
| F2 | The META ticker had belonged to the Roundhill Ball Metaverse ETF, which changed its ticker to METV at the end of January 2022 (press, for context) | CNN Business article as syndicated by WRAL, 8 June 2022 | https://www.wral.com/meta-alert-facebooks-old-fb-stock-ticker-is-no-more/20321225/?version=amp | 2026-09-28 | "there already was an exchange-traded fund that had that ticker: the Roundhill Ball Metaverse ETF"; "in mid-January, Roundhill said it was changing the ticker of its metaverse ETF to 'METV.' That took effect at the end of January." | hook; dat:pl:reference-data-and-symbology-services:meta |
| F3 | FIGI: a 12-character alphanumeric, randomly generated identifier; once assigned it never changes; a retired FIGI is never reused; a standard of the Object Management Group | OpenFIGI, About FIGI | https://www.openfigi.com/about/figi | 2026-09-28 | "a 12 character, alphanumeric, randomly generated ID"; "Once a FIGI is assigned, it never changes throughout the trade lifecycle."; "retired and never reused"; "a standard of the Object Management Group" | remark in section 3; omsources |
| F4 | ISIN is ISO 6166, "the core identifier of securities transactions and settlement"; ANNA is the association of national numbering agencies promoting ISINs | Association of National Numbering Agencies (ANNA), home page | https://www.anna-web.org/ | 2026-09-28 | "International Securities Identification Number (ISIN) - ISO 6166"; "The ISIN is the core identifier of securities transactions and settlement." | remark in section 3; omsources |

## EXCLUDED

- ISO 15022/20022 corporate-action event types (brief): not needed; the chapter's event model is generic.
- The FB ticker's later reuse (brief's hook): no source found; the hook uses the META ticker's documented passage from an ETF to Meta instead.

