# 7. C++ for Latency II: Compile Time — brief and source ledger

## Brief

- **Hook.** The handler called one virtual function per message; making the strategy a template parameter removed the indirect call, and the compiler then inlined the whole path from the decoder to the order.
- **Sections.** Virtual dispatch and what it costs; Static polymorphism: templates, CRTP and concepts; Compile-time evaluation; Inlining and its limits; Branch layout and cold paths.
- **Defines.** dynamic dispatch, static polymorphism, curiously recurring template pattern, compile-time evaluation, inlining, devirtualisation, cold path.
- **Uses (defined earlier).** branch prediction (ch2), branch misprediction (ch2), microbenchmark (ch2), hot path (ch1).
- **Tutorial.** Three dispatchers for the same message stream -- virtual calls, std::variant with std::visit, and a template pipeline -- benchmarked on predictable and on mixed message types; a lookup table computed at compile time with consteval; an error path marked cold and moved out of line, checked in the disassembly. End state: a chart of cycles per message by design and message mix.
- **Build.** `firm.pipeline`: compile-time composition of hot-path stages (decode, book, strategy, gateway) constrained by concepts, with a runtime-polymorphic adapter for tests; C++20, and a Rust twin with generics and traits. Used by chapters 20 and 26.
- **Weekend problem.** The indirect branch -- named result: the cost per message of virtual against static dispatch when the target is predictable and when it is not (a ratio, measured; the tests assert only the ordering).
- **Data.** Measured on this laptop only.
- **Facts to verify.** ISO C++20: concepts, consteval, [[likely]] (standard or cppreference); GCC manual: -fdevirtualize, function attributes cold and noinline; Driesen and Holzle 1996, The direct cost of virtual function calls in C++ (OOPSLA).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Driesen and Hoelzle, The direct cost of virtual function calls in C++, OOPSLA 1996 (ACM SIGPLAN Notices, October 1996) | Crossref record | https://api.crossref.org/works/10.1145/236337.236369 | 2026-09-25 | title, venue, date | section 1, omsources |
| F2 | GCC function attribute `cold`: the function is unlikely to be executed, optimised for size, placed in a special subsection of the text section with other cold functions for code locality of the non-cold parts; paths leading to calls of cold functions are marked unlikely | GCC 11.4 manual, Common Function Attributes | https://gcc.gnu.org/onlinedocs/gcc-11.4.0/gcc/Common-Function-Attributes.html | 2026-09-25 | "The cold attribute on functions is used to inform the compiler that the function is unlikely to be executed... placed into a special subsection of the text section" | section 5 |
| F3 | C++20: consteval (immediate functions), the attributes [[likely]] and [[unlikely]], concepts | cppreference, consteval specifier and attributes likely/unlikely | https://en.cppreference.com/w/cpp/language/consteval | 2026-09-25 | "consteval - specifies that a function is an immediate function, that is, every call to the function must produce a compile-time constant" (since C++20) | sections 3 and 5 |

## EXCLUDED

