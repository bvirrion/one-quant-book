# 23. Rust — brief and source ledger

## Brief

- **Hook.** The code looks harmless: take a reference to the best bid in a vector of levels, then push a new level, then print the reference. The compiler refuses it with error E0502, and the candidate is asked two questions: what bug in the equivalent C++ the refusal just prevented, and how to write the function so it compiles without cloning the book.
- **Sections.** Ownership and borrowing, and the errors that teach them; Lifetimes in signatures and structs; Traits, generics and dynamic dispatch; Unsafe, Send and Sync: what the guarantees are and where they stop.
- **Defines.** none (the chapter uses the vocabulary of Books 1-17, listed below).
- **Uses (defined earlier).** data race (B13.9), zero-cost abstraction (B13.9), sound abstraction (B13.9), bounds-check elimination (B13.9), global allocator (B13.9), async runtime (B13.9), dynamic dispatch (B13.7), undefined behaviour (B13.8), atomic operation (B13.11), memory ordering (B13.11), output-prediction question (ch22).
- **Question bank.** 13 questions, 4/5/4. Families: 'does this compile, and why not' (borrow conflicts E0502 and E0499, use after move E0382, a returned reference to a local E0106/E0515) -- each checked by rustc's error code; fixing a borrow error without cloning (splitting borrows, indices, entry API); lifetimes in a parser struct over a byte buffer; traits (static against dynamic dispatch for a strategy interface; object safety); output prediction (drop order of a struct's fields and of temporaries; shadowing); Send and Sync (why Rc is not Send, what makes a type Sync); an unsafe block's invariants (a sound get_unchecked wrapper) -- the soundness argument in the solution, Miri not required; a lock-free counter with the right orderings. Roles: developer 11, researcher 1, mle 1. Firms: market maker 4, proprietary firm 4, crypto firm 3, any 2.
- **Facts to verify.** The Rust Reference and the Rustonomicon (versions for the pinned 1.97.1 toolchain) for each rule cited; rustc error index entries for the error codes.
- **Data.** Figures: none planned. Code: rust/ Cargo crate iv_rust (no dependencies; the coding answers with unit tests; clippy -D warnings); rust/snippets/*.rs (compile-fail and output-prediction snippets); tests/test_solutions.py runs rustc --edition 2021 on each snippet and asserts the error code or the stdout.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | rustc error codes E0106 (missing lifetime specifier), E0277 (trait bound not satisfied), E0382 (use of moved value), E0499 (two mutable borrows), E0502 (mutable borrow while immutably borrowed), E0515 (return reference to local) | Rust compiler error index; asserted by compiling each snippet with the pinned rustc 1.97.1 | https://doc.rust-lang.org/error_codes/error-index.html | 2026-09-29 | the codes emitted by rustc 1.97.1 on the chapter's snippets (tests/test_solutions.py) | section 1-4; questions 1-6, 11 |
| F2 | Drop order: local variables in reverse declaration order, struct fields in declaration order | The Rust Reference, Destructors | https://doc.rust-lang.org/reference/destructors.html | 2026-09-29 | "The fields of a struct are dropped in declaration order"; "variables ... are dropped in reverse order of declaration" (confirmed by the drop_order snippet's output) | section 3; question 7 |

## EXCLUDED

