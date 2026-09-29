# 22. C++ — brief and source ledger

## Brief

- **Hook.** 'What does this print?' Eight lines: a base class with a virtual function called from its constructor, a derived class that overrides it, one object. The candidate answers 'Derived', explains dynamic dispatch well, and is wrong: during the base's constructor the object is still a base, and the base's version runs.
- **Sections.** Object lifetime: construction, destruction, temporaries and dangling references; Moves, copies and value categories; Templates and compile-time code; Undefined behaviour, and what the standard library does inside.
- **Defines.** output-prediction question.
- **Uses (defined earlier).** undefined behaviour (B13.8), strict aliasing (B13.8), dynamic dispatch (B13.7), curiously recurring template pattern (B13.7), compile-time evaluation (B13.7), small-buffer optimisation (B13.6), structure padding (B13.6), object pool (B13.6), data race (B13.9), atomic operation (B13.11), memory ordering (B13.11), cache line (B13.3), false sharing (B13.3).
- **Question bank.** 14 questions, 5/5/4. Families: output prediction (virtual call in a constructor; destruction order of members and temporaries; overload resolution with an rvalue; copy elision; static initialisation order within a translation unit; integer promotion in a comparison); find the undefined behaviour (a dangling string_view, signed overflow in a loop bound, a use after move of a moved-from vector's contents left unspecified, an iterator invalidated by push_back) -- stated, then diagnosed by sanitizers; moves (write a correct move constructor and assignment for a buffer; rule of zero, three, five); templates (a constexpr computation, a concept constraining an order type); library internals (vector growth and invalidation, unordered_map buckets, why std::function allocates); a short design question (a fixed-capacity ring buffer's interface). Roles: developer 13, researcher 1, mle 1. Firms: market maker 6, proprietary firm 5, bank 1, any 3.
- **Facts to verify.** ISO/IEC 14882:2020 (C++20) clauses cited for each behaviour (the draft N4861 is public); cppreference as secondary; implementation-defined results stated for x86-64 Linux with g++ 11 and 13 (the CI compiler).
- **Data.** Figures: none planned (one small table: value categories). Code: cpp/snippets/*.cpp (one file per output-prediction or UB question, ASCII only), cpp/iv_cpp_test.cpp (the coding answers: buffer with moves, ring buffer, constexpr and concept answers); tests/test_solutions.py compiles each snippet at -O0 and -O2 with -std=c++20 -Wall -Wextra and asserts stdout; UB snippets are built with -fsanitize=address,undefined and the test asserts the diagnosis, no output.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Working Draft, Standard for Programming Language C++, N4861 (2020-04-01), the public draft closest to ISO/IEC 14882:2020 | open-std.org WG21 document register | https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2020/n4861.pdf | 2026-09-29 | document number and title (rules cited: [class.cdtor] virtual calls during construction, [class.temporary] lifetime of temporaries, [expr.const] no UB in constant evaluation, [basic.start.dynamic] initialisation order) | omsources; section 1, 3 |

## EXCLUDED

Implementation-defined results (sizes, the moved-from vector being empty, 32-bit unsigned) are asserted for g++ with libstdc++ on x86-64 Linux and labelled as such in the text.

