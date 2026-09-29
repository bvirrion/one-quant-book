# 23. Commercial Relationships with Venues, Brokers and Vendors — brief and source ledger

## Brief

- **Hook.** A venue offers a market-maker programme: a fee discount in exchange for quoting obligations and a volume commitment. For a small firm, meeting the obligations costs more than the discount is worth; for a large one they cost nothing it was not already doing. The same terms are a different deal for each.
- **Sections.** What is negotiable; Market-maker programmes and tiers; Clearing, prime-brokerage and connectivity contracts; Leverage: what a firm of each size has.
- **Defines.** best alternative to a negotiated agreement, reservation value, zone of possible agreement, volume commitment, shortfall penalty.
- **Uses (defined earlier).** volume tier (B1.29), incentive programme (B1.30), market-maker appointment (B1.30), designated market maker (B1.29), quoting obligation (B1.24), tier cliff (B11.17), marginal fee (B11.17), rebate capture (B11.17), bargaining power (B10.23), clearing broker (B1.29), executing broker (B1.29), prime broker (B1.6), uptime requirement (B3.25), tier matching (B3.25), token market-making agreement (B3.24), service-level agreement (B14.15), cross-connect (B14.9), most-favoured-nation clause (ch4), house margin (ch14), enterprise licence (ch22).
- **Tutorial.** A firm evaluates a venue's market-maker programme (a fee discount, obligations on presence and width, a volume commitment with a shortfall penalty): cost the obligations with Book 11's quoting model, evaluate tier qualification with firm.feesched, compute its reservation value and the venue's, and split the zone of agreement by Nash bargaining for a small and a large firm. End state: a chart of the programme's net value against the firm's volume, with the zone of agreement.
- **Build.** `firm.dealterms`: deal packages as data (rates, tiers, obligations, commitments, penalties, term), valuation against the firm's activity (through firm.feesched and firm.mmecon), reservation values, the zone of possible agreement and a Nash bargaining split with outside options; Python.
- **Weekend problem.** The programme -- named result: the volume above which a market-maker programme's discount pays for its obligations, and the Nash-bargaining fee that a small and a large firm each obtain.
- **Facts to verify.** a published market-maker programme of an exchange (terms, obligations, benefits), from the exchange's circular or rule filing (dated); a crypto venue's market-maker programme terms (pointer to Book 3 ch. 25) (dated); Fisher and Ury 1981, Getting to Yes (BATNA); Nash 1950, The bargaining problem (Econometrica); Raiffa 1982, The art and science of negotiation; a clearing broker's published fee schedule or a CFTC/SEC fee-programme rule filing (dated).
- **Data.** Synthetic; dated boxes for programme terms.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Nasdaq, SR-NASDAQ-2025-088 (SEC Release 34-104181; Federal Register 90 FR 52123, 19 November 2025), Qualified Market Maker Program: currently an additional rebate of $0.000075 per share executed in Tapes A and C ($0.00005 in Tape B) if the MPID adds liquidity above 1.25% of consolidated volume in the month, quotes at the NBBO at least 50% of the time in an average of at least 2,700 symbols a day (and 1,200 Tape A symbols), and has increased its added liquidity by at least 0.50% of consolidated volume relative to May 2020; the filing proposes instead $0.0001 per share for QMMs qualifying for the Tier 2 rebate that add above 0.325% of consolidated volume with at least a 95% ratio of adding to total activity, and a new $0.0027 credit for midpoint liquidity to members adding 20 million shares a day or more | Federal Register full text | https://www.federalregister.gov/documents/full_text/text/2025/11/19/2025-20255.txt | 2026-09-28 | "an additional rebate of $0.000075 per share executed in Tapes A and C and $0.00005 per share executed in Tape B"; "above 1.25% of Consolidated Volume"; "quotes at the NBBO at least 50% of the time during the month during regular market hours in an average of at least 2,700 symbols per day"; "the amount of the rebate would increase to $0.0001 per share executed"; "above 0.325% of Consolidated Volume"; "at least a 95% ratio" | hook; dat:fm:commercial-relationships-with-venues-brokers-and-vendors:qmm; tutorial |
| F2 | J. F. Nash, "The Bargaining Problem", Econometrica 18(2), 155-162, April 1950 | Crossref | https://doi.org/10.2307/1907266 | 2026-09-28 | bibliographic | section 1 |
| F3 | R. Fisher and W. Ury (with B. Patton), Getting to Yes, 1981 | Open Library | https://openlibrary.org/works/OL1837566W | 2026-09-28 | bibliographic | section 1 |
| F4 | H. Raiffa, The Art and Science of Negotiation, 1982 | Open Library | https://openlibrary.org/works/OL2620276W | 2026-09-28 | bibliographic | section 1 |

## EXCLUDED

- A crypto venue's market-maker programme: pointer to Book 3 chapter 25 only.
- A clearing broker's published fee schedule: not fetched; clearing terms are discussed generically.
- Consolidated volume of about 12 billion shares a day: an input, not a sourced figure.

