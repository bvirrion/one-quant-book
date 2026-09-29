# 19. Pricing-Library Architecture — brief and source ledger

## Brief

- **Hook.** A client asked on Friday for a price on an autocallable with a memory coupon and a lookback on the knock-in; the library had no class for it. By Monday it was priced from twenty lines of payoff script, on the same models, market objects and Monte Carlo engine as every other trade.
- **Sections.** The analytics library and its layers; Instruments, market objects, models and engines; Payoff scripting; Lazy recalculation and observers; Bindings to other languages.
- **Defines.** analytics library, market object, payoff scripting language, payoff script, observer pattern, lazy recalculation.
- **Uses (defined earlier).** pricing engine (B5.28), market-data snapshot (B5.28), bump-and-reprice (B5.4), Greeks (B5.4), reference pricer (B5.28), autocallable (B5.18), memory coupon (B5.18), Monte Carlo method (B4.26), adjoint mode (B4.28), language binding (ch9), application binary interface (ch9), canonical trade model (ch21).
- **Tutorial.** Write a small payoff language -- a tokenizer, a recursive-descent parser, an abstract syntax tree, an event schedule extracted from it -- and evaluate scripts on paths from Book 5's Monte Carlo engine with its market-data snapshots, first by interpreting the tree per path and then by compiling it to array expressions over all paths; price a European, an Asian, a barrier and an autocallable by script and compare with the library's own engines; show the observer pattern refreshing a curve-dependent price. End state: a table of script against library prices with Monte Carlo errors, and the interpreter's cost against the compiled version.
- **Build.** `firm.payoffdsl`: grammar (observation dates, arithmetic, comparisons, if/else, state variables, pays), parser with error positions, event-schedule extraction, a per-path interpreter and a vectorised compiler, an engine registered with firm.pricing (`register`) so that scripted instruments price, bump and batch like any other, with common random numbers (INTERFACES.md section 1); Python.
- **Weekend problem.** Priced by Monday -- named result: the scripted autocallable's price and delta against firm.pricing's own autocallable engine on common random numbers, their difference in standard errors, and the speed-up of the compiled script over the interpreted one.
- **Facts to verify.** QuantLib documentation or Ballabio, Implementing QuantLib: instruments, pricing engines, observers, handles; Andreasen and Savine (or Savine 2018, Modern Computational Finance): scripting of payoffs; Gamma, Helm, Johnson and Vlissides 1994, Design Patterns: observer; a public description of a bank's payoff language (paper or talk, dated).
- **Data.** Book 5's firm.pricing market data and engines; synthetic market snapshots.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | QuantLib LazyObject: "Framework for calculation on demand and result caching"; it is both an Observer and an Observable | QuantLib reference documentation, class QuantLib::LazyObject | https://www.quantlib.org/reference/class_quant_lib_1_1_lazy_object.html | 2026-09-28 | "Framework for calculation on demand and result caching."; inherits from Observable and Observer | section Lazy recalculation; omsources |

## EXCLUDED

- Savine (2018), payoff scripting books: not found on Crossref; not cited.
- Gamma, Helm, Johnson and Vlissides 1994: the observer pattern is described generically, no claim about the book.
- A public description of a bank's payoff language (brief): not searched.

