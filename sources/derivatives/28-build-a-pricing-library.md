# 28. Build: A Pricing Library — brief and source ledger

## Brief

- **Hook.** A risk manager asks for the book's vega to the one-year 90% strike; the answer needs every pricer the firm owns to accept the same bumped surface, and half of them cannot.
- **Sections.** Instruments, models and engines; Market data as an immutable snapshot; Greeks, bumps and scenarios; Testing a pricer; Build: the library.
- **Defines.** pricing engine, market-data snapshot, reference pricer.
- **Uses (defined earlier).** bump-and-reprice (ch. 4), P\&L attribution (Book 1 ch. 7), the curve of Book 2 ch. 9 (`firm.curve`), stress test, historical scenario, hypothetical scenario (Book 6 ch. 22), risk engine (Book 6 ch. 29), every component of chapters 1-27.
- **Tutorial.** Wire the book's components into one library: price a small book (vanilla, American, barrier, variance swap, autocallable) through one call, produce bucketed vega by bump-and-reprice with common random numbers, and run a ten-scenario grid.
- **Build.** `firm.pricing`: the pricing library (Instrument, MarketData, Model, Engine, registry, price(), greeks(), scenario hooks) in Python; core types with the Black-Scholes and finite-difference engines also in C++20 and Rust; Book 6 ch. 29's risk engine runs on it.
- **Weekend problem.** The vega nobody could compute — named result: the book's bucketed vega at the one-year 90% strike, and the Monte Carlo noise in it with and without common random numbers.
- **Facts to verify.** QuantLib architecture (Instrument, PricingEngine, Handle; quantlib.org documentation); Open Source Risk Engine design (ORE documentation); trade representation standards (FpML, ISDA CDM).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | QuantLib's Instrument is an abstract class defining the interface of concrete instruments; setPricingEngine sets the pricing engine; NPV returns the net present value; Instrument derives from LazyObject, which caches the results of the previous calculation and registers as observer of the objects it depends on so that calculations are performed again when they change (reference documentation, QuantLib 1.43) | QuantLib reference, class QuantLib::Instrument | https://www.quantlib.org/reference/class_quant_lib_1_1_instrument.html | 2026-09-24 | class description and method docs (quoted) | sec. instruments, models and engines; sec. market data |
| F2 | Open Source Risk Engine (ORE) provides risk analytics and value adjustments, with interfaces for trade and market data and system configuration (API and XML); it is built on QuantLib, which it extends with simulation models, instruments and pricing engines; Modified BSD licence | ORE repository README | https://github.com/OpenSourceRisk/Engine | 2026-09-24 | README (quoted) | sec. instruments, models and engines |
| F3 | FINOS Common Domain Model: a model for financial products, trades in those products and the lifecycle events of those trades; an open source standard available as code in multiple languages; open-source availability announced by FINOS with ISDA, ICMA and ISLA in February 2023 | FINOS CDM repository description; FINOS press release | https://github.com/finos/common-domain-model | 2026-09-24 | repository description (search excerpt); https://www.finos.org/press/finos-launches-common-domain-model-project-in-partnership-with-isda-isla-and-icma | dat:dv:build-a-pricing-library:standards |
| F4 | FpML (Financial products Markup Language) is the open source XML standard for electronic dealing and processing of derivatives; version 5.13 is the Recommendation, 5.14 a Last Call Working Draft (24 August 2026) | fpml.org home page | https://www.fpml.org/ | 2026-09-24 | home page (quoted) | dat:dv:build-a-pricing-library:standards |

## EXCLUDED

- No firm-specific pricing-library architecture is described: none has a citable public source beyond the open-source projects above.
