# firm.connplan

The connectivity plan of One Quant Book 14, chapter 29: from venues, latency targets and a footprint to a
latency table, a bill of materials, contracts, a disaster-recovery line, an annual budget with sensitivities,
the unmet targets with the cheapest change that meets each, and checks on every price row.

## The exported cost table (read by Book 16's `firm.techtier`)

`firm_connplan.export_cost_table(plan, path)` writes, and `data/cost_table.csv` holds for the chapter's plan, one
row per bill-of-materials line:

| column | meaning |
|---|---|
| `item` | the product bought |
| `vendor` | who sells it (a venue, a cloud, or `carrier` for an unnamed telecom provider) |
| `venue` | the plan's venue the line serves (or `shared`) |
| `category` | `colocation`, `connectivity`, `market data`, `cloud`, `disaster recovery` |
| `qty` | units bought |
| `monthly_usd` | recurring cost a month for the quantity |
| `one_time_usd` | one-time cost for the quantity |
| `annual_usd` | twelve months plus one-time amortised over the term (36 months by default) |
| `source` | the ledger row that publishes the price (`networks/NN:Fk`); empty when the price is an assumption |
| `as_of` | the date the price was read (`YYYY-MM-DD`) |

Rows with an empty `source` are assumptions the firm must replace with a quote; `check_prices` lists them, and
rows older than 60 days, before a plan is used. Prices are in USD; nothing in the table is converted.
