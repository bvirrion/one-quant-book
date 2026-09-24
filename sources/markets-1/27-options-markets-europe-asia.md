# 27. Options Markets in Europe and Asia — brief and source ledger

## Brief

- **Hook.** In 2024 more index option contracts traded in Mumbai than everywhere else combined.
- **Sections.** Europe; Korea; India; Other Asian markets; The expiry-day case.
- **Defines.** lot size (derivatives), notional turnover, premium turnover, weekly expiry, position limit.
- **Tutorial.** Contract counts versus notional versus premium: three rankings of the same markets.
- **Build.** Turnover normaliser.
- **Weekend problem.** Counting contracts — named result: premium turnover ratio between two markets.
- **Facts to verify.** FIA 2023/2024 volume by exchange; NSE index option lot sizes and changes; SEBI interim order July 2025 (Jane Street) facts; SEBI F&O retail loss study; Kospi 200 multiplier history.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | SEBI study (press release 23 Sept 2024): 93% of individual traders incurred losses in equity F&O between FY22 and FY24; aggregate losses exceed Rs 1.8 lakh crore over three years | SEBI press release | https://www.sebi.gov.in/media-and-notifications/press-releases/sep-2024/updated-sebi-study-reveals-93-of-individual-traders-incurred-losses-in-equity-fando-between-fy22-and-fy24-aggregate-losses-exceed-1-8-lakh-crores-over-three-years_86906.html | 2026-09-18 | title of the release | dat:m1:options-markets-europe-asia:sebi; pb q15 |
| F2 | SEBI circular SEBI/HO/MRD/TPD-1/P/CIR/2024/132 of 1 Oct 2024: index derivative contract value Rs 15-20 lakh at review (from 20 Nov 2024); one weekly-expiry benchmark index per exchange; upfront collection of option premium; removal of calendar spread benefit on expiry day; additional 2% ELM on short options on expiry day; intraday monitoring of position limits | SEBI circular as summarised by brokers and the exchange circulars (search excerpts) | https://www.cse-india.com/upload/upload/Oct_011024.pdf | 2026-09-18 | quoted excerpts | dat sebi |
| F3 | SEBI interim order of 3 July 2025 against Jane Street group entities: alleged index manipulation on expiry days from January 2023; impounding of Rs 4,843.57 crore; the group deposited the amount on 14 July 2025 while reserving its right to challenge | Oxford Business Law Blog, July 2025; Legal 500 summary | https://blogs.law.ox.ac.uk/oblb/blog-post/2025/07/jane-street-and-expiry-day-trap-unpacking-sebis-crackdown-algorithmic | 2026-09-18 | "deposited the full amount on July 14, 2025, while reserving its right to challenge the order" | dat sebi (firm unnamed in the text; named only in the source's title under Sources); section expiry-day case |
| F4 | On 14 June 2012 the contract size of KOSPI 200 options (and the linked Eurex product) was raised from KRW 100,000 to KRW 500,000 | Eurex news (search excerpt) | https://www.eurex.com/ex-en/find/news-center/news/Eurex-and-Korea-Exchange-further-expand-their-link-with-Korean-Won-contract-2712630 | 2026-09-18 | "raised ... from 100,000 KRW to 500,000 KRW" | dat:m1:options-markets-europe-asia:kospi |
| F5 | FIA 2025 regional volumes and year-on-year changes | chapter 22 ledger F1 | https://www.fia.org/fia/articles/etd-volume-december-2025 | 2026-09-18 | 2024 regional figures are DERIVED from the published changes; the derived total, 206.4bn, reproduces the published -42.2% (asserted) | hook; fig regions; exo 4 |
| F6 | KOSPI 200 options: highest volume of any derivatives product in the world in 2000 (194m contracts); at the top of the FIA volume tables for almost a decade; 3.67bn contracts in 2011 | Mondo Visione (KRX release, 2001); FIA MarketVoice commentary on the KOSPI 200 (search extracts) | https://www.fia.org/marketvoice/articles/commentary-morphing-us-treatment-kospi-200-futures | 2026-09-19 | "at the top of the FIA's volume tables for almost a decade" | hook; section Korea |

## EXCLUDED

- The brief's hook ("more index option contracts traded in Mumbai than everywhere else combined"): exchange-level FIA rankings not fetched; replaced by the regional shares.
- "KOSPI 200 options were the world's most traded derivative in the 2000s": widely stated, not fetched; kept as one qualitative sentence. RESOLVED 2026-09-19 in the front-to-back read: see F6.
- The later KOSPI multiplier cut (2017) and the size of the post-2012 volume fall: not verified; the text now says only what arithmetic implies.
- Number of individual F&O traders (about 1 crore) and the split of profits between proprietary traders and FPIs: in the SEBI study, seen only in search excerpts; the solution says "proprietary firms and foreign investors, largely algorithmic" without amounts.
- Details of the alleged trading pattern and the example days in the interim order: not reproduced; the chapter analyses the generic structure and states that the matter is undecided.
- European block-trade share, the warrants/certificates market, and the retail share in Taiwan, Japan and Hong Kong: qualitative statements, no numbers.
- M1-M4 and all fee, tax and spread levels in the weekend problem are invented and declared so.
