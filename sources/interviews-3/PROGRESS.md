# Progress: interviews-3

Binding rules: `sources/INTERVIEW_BOOKS.md`, run file `sources/BATCH_BOOKS_18-20.md`, chapters `outline/interviews.md`.
Update this file after every chapter. A fresh agent resumes from here alone.

**State (2026-11-03): the book is complete. All nine chapters, 390 questions, 391 pages (1.00 pp/q), median answer 259 words; under the 430-page flag, so no question was cut.**

Final checks, as last run on the final build: log 0/0/0; `check_interview_book.py interviews-3 --final` GREEN; `--cross` GREEN (1,789 stems); `check_omcode.py` 1,500 listings, 0 problems; `OQB_TESTS=fast tools/test_code.sh interviews-3` TEST-CODE GREEN (ruff and clippy included); pytest on `code/interviews-3` 386 passed, 0 failed, 0 skipped, three runs in a row, on this machine. CI lacks the Java, C#, solc and EVM tools, so those tests skip there with a stated reason; that path was not run. 399 listings, 56 breaks, 0 orphans, none wrapped, by text scan (round 2).

| Chapter | Questions | Stars | Pages (question + answer) | State |
|---|---|---|---|---|
| 01 algorithms | 80 | 16/32/20/12 | 12 + 55 = 67 | done; median 240 |
| 02 python-and-pandas | 40 | 9/20/8/3 | 10 + 20 = 30 | done; median 236 |
| 03 cpp | 60 | 12/28/15/5 | 34 + 31 = 65 | done; median about 240 |
| 04 low-latency | 35 | 5/14/11/5 | 20 + 18 = 38 | approved pilot; median 231 |
| 05 operating-systems-concurrency-and-networks | 40 | 8/20/9/3 | 21 + 22 = 43 | done; median 265 |
| 06 system-design | 40 | 8/20/9/3 | 8 + 25 = 33 | done; median 288 |
| 07 sql-and-data | 25 | 6/11/6/2 | 9 + 15 = 24 | done; median 243 |
| 08 smart-contracts-and-crypto-engineering | 30 | 6/15/7/2 | 13 + 19 = 32 | done; median 293 |
| 09 reading-debugging-and-software-design | 40 | 9/20/9/2 | 24 + 22 = 46 | done; median 290 |

Page counts are from the final PDF; their sum, 378, leaves out 9 pages of front matter and index.

Macros added to the entry file (for the main session to fold in): none.

Unverified claims (rest on the ledger only, not run here):
- PostgreSQL behaviour in 07 (no server on this machine): rows S1, S2, S3.
- In 09: Java `volatile` as the fix for double-checked locking (no test can force the reordering), Clang MemorySanitizer and Valgrind Memcheck (R36, neither run), Protobuf rules (R43), the C++23 range-for rule (R16: the draft; g++ 11.4 in C++20 mode shows only the old behaviour).
- Java and C# ARE run: Java 11 through the single-file launcher `java File.java` (a JRE with `jdk.compiler`, no `javac` binary), C# through `~/.dotnet/dotnet` SDK 8.0.424 offline. Their tests skip with a reason if the tools are absent. So CI, which installs neither, skips them.

Tooling notes:
- Answer listings: question listings print "Listing C.N", where C is the printed chapter from `part.tex`. Answer listings print plain "Listing N", because the chapter counter is 0 in the appendix and the counter is never reset, so they continue from the last chapter's question-listing count and run on through all answers (now 41 to 102). Numbers are unique and hyperref anchors do not collide, but the start depends on the last chapter. One line for the main session, in the entry file after `\appendix`: `\setcounter{lstlisting}{0}`. Not done: it is outside this book's write paths.
- Long chapter directory: in 09 the source path does not fit on the caption's line, so listings stretched the caption across the box. Every 09 caption ends `\protect\hfil\protect\break`, which puts the path on its own line. Use the same in any chapter with a directory this long (05 will need it).
- `\texttt{--x}` prints one hyphen: write `-{}-x`.
- Buggy-on-purpose Python carries `# ruff: noqa: Bxxx` on line 1, and the listing prints from line 2.
- ASan does not see an erase inside a range-for over `std::map`: the step is in `_Rb_tree_increment`, in the uninstrumented `libstdc++.so`. `-D_GLIBCXX_DEBUG` does.
- libstdc++ 11's `std::visit` is an indirect call through a table (asserted only on g++ 11 in the test).

Chapter 01 is merged. To insert questions in any chapter later: `sources/interviews-3/renumber.py <chapter>` works for 01; see its docstring.

Listing-page checks (rule narrowed by the main session: per chapter, every page where a listing breaks, plus about one listing page in four, 130 dpi; text scans for the rest).
- Answers flow with no page break between chapters, so a break's place moves when anything earlier changes, and fixing an orphan moves every later break. Hence: per chapter, read the one-in-four sample now, and text-scan captions and breaks; read the break pages at the final build, after the orphans are fixed, for all chapters.
- 01: 55 listing pages, 21 breaks by text scan. Read in full at 130 dpi: PDF pages 84, 90, 95, 108, 111, 117, 123, 127 (8 of the 14 the rule asks for); 8 stretched captions found by scan and fixed, one seen in an image first. All listings OK apart from those. Break pages: at the final build.

Dropped from 09, to use in 03: `shared_ptr` cycle, `string_view` to a temporary, signed-overflow check, C# struct boxing. (`dict.fromkeys` aliasing is in 02.)

Rule slip, 2026-11-02: while writing 02, a shell line that lost its directory variable started a repo-wide pytest. It ran about three minutes before it was stopped. Nothing outside the ruff cache changed, by a modified-file scan. Report this.

02 notes:
- Read at 130 dpi: PDF pages 21, 142, 146, 150, 153 (5 of the 6 the sample asks for). Breaks by text scan only so far; they are read at the final build.
- Not run here, on the ledger: Python 3.13 free threading (P5), Python 3.12's `sum` (P14), pandas 3 copy-on-write (P10), a direct `malloc` invisible to `tracemalloc` (P16). The zero speed-up of threads rests on P4, with no timing asserted. The Python docs say a list default in a dataclass raises `TypeError`; 3.10.12 raises `ValueError`, and the book prints what ran (P8).
- Pandas 2.3.3 surprise, tested: after a 1e9 in `x`, `rolling(50).var()` is -2.6 for every later row and `rolling.corr` NaN, while `rolling.cov` stays right. That is a version-pinned assertion (Q40).
- Python 3.10 trap for any later chapter: a `SharedMemory` attached from an unrelated process registers it with that process's resource tracker, which removes it on exit. The test uses a fork.

03 notes:
- Read at 130 dpi: PDF pages 48, 208, 214, 216, 220 (5 of about 16 the sample asks for; all breaks are read at the final build). `lsplit.py` lists false breaks on question pages because `#include <iostream>` matches an earlier page: only the answer-side breaks are real.
- Run here, g++ 11.4: every printed C++ program, ASan/UBSan and TSan on the bugs, C# through .NET 8. Broken twins are built by the tests (pool that reads `next` late, vector that always moves, optional that sets the flag first, variant with no destroy, relaxed decrement, expression template stored by value).
- Ledger only: what the standard promises (rows C1-C34), `std::atomic<shared_ptr>` in GCC 12 (C30; g++ 11.4's refusal is run), Boost's fence form of the count (C35). No timing is claimed anywhere.
- Trap for later chapters: `std::runtime_error("x")` allocates through `operator new`, so a no-heap driver must throw an empty struct.

## Chapter 05 notes (2026-11-03)

- 39 tests + NONNUMERIC Q33; pytest 17 s; ruff clean; gate GREEN and log 0/0/0 at this build; 322 PDF pages for 320 questions. Ledger O1 to O45.
- Tests caught a real defect in writing: `table_bytes` stopped at the first level with one table and undercounted 1 GiB (2,101,248 against the right 2,109,440). Fixed, with a slow page-by-page count as the differential.
- Run here: all programs on loopback (WSL2 kernel 6.18), twins: rwlock without the writer check (prints 1), futex back to state 1 (hangs, hits the timeout), shm ring relaxed (TSan reports a race). Model only, no packet capture or wire: Nagle (`iv_nagle`), reliable delivery, arbiter, inversion.
- Not verified here, ledger only: the receive path of Q33; IGMP on a real switch (Q26); fsync surviving a real power cut (Q18). softnet_stat's second column: now sourced from the kernel's `net-procfs.c` (row O46, added at the final pass), read from source only, not provoked here.
- `parts/interviews-3/preface.tex`: `\hfuzz=1.5pt` around the generated role table, which is 1.1 pt too wide now that chapter 05's long title is in it. tools/ untouched.
- Pages read at 130 dpi: PDF 84, 91, 95, 101, 264, 273, 276, 281 (8 of 34 listing pages); no layout defect but the orphan lines listed for the final build. Breaks now: five_tuple 2+9, udp_drop 2+19, iv_waitfor 2+13, iv_window 8+1, rwlock 35+1, iv_nagle 32+2, iv_event_loop 8+1, shm_ring 20+1; all move with later edits.

## Chapter 06 notes (2026-11-03)

- 34 tests + NONNUMERIC Q6, Q12, Q17, Q28, Q31, Q37; pytest 3 s; ruff clean; gate GREEN, log 0/0/0; 354 PDF pages for 360 questions. Ledger S1 to S11. Median 288 words, above the 220 aim: design answers carry several parts. Not padded, not cut.
- Tests caught: `Order.on` increased `filled` before raising on an overfill (fixed); a day of the market data service was 7.5 TB in the first draft, 750 GB in truth (fixed).
- Everything is a model or arithmetic on the stem's numbers. Nothing ran on a network or venue. Real: Parquet and DuckDB pruning (Q18), SQLite transactions and threads (Q23). At 99% load the queue simulation has not settled (79 against 100); the answer says so.
- Pages read at 130 dpi: PDF 110, 295, 300, 305, 314 (5 of 23 listing pages). Found one wrapped comment in a question box (iv_fencing line 20), fixed. Question-box listings are narrower than the gate's 94 characters.

## Chapter 08 notes (2026-11-03)

- 30 tests (test_q1 to test_q29 plus test_q14_model), about 1.6 s; Q30 is NONNUMERIC. Ledger X1 to X21. Median 293 words.
- Tools: solc 0.8.28 and @ethereumjs/evm 10.0.0 under `build/iv38/node/node_modules`, installed with `npm install --ignore-scripts`, no account or e-mail. `build/` is not part of the book, so the EVM tests skip with a stated reason where it is absent, CI included. Every vulnerable contract runs on that local EVM or a model, and nothing touches a deployed contract.
- `.sol` has no language in `styles/onequant.sty` and prints with C++ highlighting (shared file, not touched).
- Tests caught: the AMM's expected constant came from a float input (now 1992013962079806432986); test_q16 read the accumulator in the past; test_q27's bisection bound was too low when margin is below maintenance; vacuous assertions replaced (alarms, Merkle twin forging). Reading caught: stem Q3 called the true answer "small" though mulFirst(2^255,2,2) is 2^255.
- Not verified here, ledger or reasoning only: real block builders and private channels, layer 2 fee formulas, threshold signing, venue index and auto-deleveraging rules, feed updating and sequencer checks. Design answers Q29 and Q30 are unmeasured.

## Final pass (2026-11-03)

- Orphans: a batch of fixes does not converge, since answers flow without page breaks and each fix moves every later break. Clean restart, front to back, one fix per build: 24 negative `\enlargethispage{-N\baselineskip}%` lines before an `\omcode` line, N = k+1 for a head orphan of k lines and N = 3 for a tail orphan (the caption sits below the code, so a one-line tail also strands it). Stale ones only leave a few lines' gap.
- Read at 130 dpi on the final layout: all 65 break pages, as cropped stitches only (bottom 27% of the page before + top 27% of the break page), which is less than the rule's whole page. Two stretched captions found (Listings 120, 128); a scan then fixed 8 in all.
- One-in-four sample, 45 whole pages (side margins cropped): PDF 25, 32, 38, 45, 51, 58, 64, 68, 72, 75, 79, 92, 113, 117, 128, 135, 139, 143, 147, 151, 154, 163, 172, 181, 191, 200, 209, 228, 242, 254, 262, 266, 270, 276, 281, 295, 317, 332, 336, 340, 344, 356, 370, 380, 385. No defect. Four stems reworded after this reading (below); same page count, 0 orphans and 0 wrapped by rescan, not re-read as images.
- The last full pytest found two real faults that chapter-by-chapter runs hid. (1) Chapters 01 and 02 both had `iv_as_of.py`, and collected together one imported the other's module: 02's is now `iv_merge_asof.py`. (2) The originality gate had 9 hits on 4 phrases, against Book 5 ch. 22, Book 13 ch. 7, Book 15 ch. 6 and one harvest row, in stems of 02, 03 and 08: all reworded. So run pytest over the whole code root before closing a chapter, not one chapter directory.
- Changed at this pass and tested in the same full run: `03-cpp/cpp/pmr_use.cpp` and `04-low-latency/cpp/count_new.cpp` (long lines split, listing ranges updated).
- Firm names: a text scan of the final PDF for 31 names of trading firms, banks, venues and protocols. The one hit is a false positive, `Sig` as a C++ template parameter. A list scan, not proof, though no firm was written in.

## End-check fixes (2026-11-03)

- Worked through three lists: an expert reader's 21 findings on chapters 05, 06, 08; 24 cold-read flags on the stems; the main session's own reading (06.39, 06.40, 08.29, 08.30, 02.39, 03.58). A later search for answers that lean on another question also changed 06.30, 01.73 and 03's `-Werror` line.
- Bugs in printed code, each with a test seen failing on the old code: server death in `iv_event_loop.py` (a reset in `flush`, a bad length in `feed`), negative amount in `iv_ledger.py`, zero tail in `iv_journal.py`, oversized secret in `iv_shamir.py` (field now 2^521 - 1, checked by Lucas-Lehmer). `iv_oracle.py` now runs in units of 10^18: 4837 and -63 were whole-token rounding.
- Trap: the old 05.38 test printed "so the server must queue replies", and `out` never held a byte, as the kernel's buffers took everything. With small buffers on the listener and the client it queues for real, and that exposed a second bug: a half-closed client lost its replies. The server now stops reading at EOF, sends what is in `out`, and then closes. Assert that a stress test reached the state it claims to test.
- `first_write.py` now waits with a `poll` that asks for no event, as a `select` for reading returns at once on the FIN.
- `header.rs` compressed so that the whole program prints with its closing brace: `#![allow(dead_code)]` on line 1, unprinted, and the fields no longer read at the end.
- New unprinted files: `05-.../cpp/cow_huge.cpp`, and contract `SlotTwice` in `Slot.sol` (below the printed range). New ledger row O47.
- Orphan pass redone from a clean state, one fix per build: 7 builds, 29 `\enlargethispage` lines now. The scan is the fix session's own script: a head or a tail of at most 2 lines counts as an orphan; on the build before these fixes it found 65 breaks and 0 orphans.
- Read at 130 dpi on the final build: whole PDF pages 53, 77, 99, 101, 302, 303, 318, 323, 352, 360, and cropped stitches (bottom 30% + top 30%) of the 25 new or moved breaks. No defect. The other 36 breaks did not move relative to their listing and were not re-read. Stale `\enlargethispage` lines were left, as they only leave a small gap.
- Open: of 7 whole pytest runs at the end, 6 gave 386 passed and one gave 1 failed, 385 passed. Its name was lost, as that run's output went through `tail -1`, and it did not come back. 25 runs of the changed chapter 05 tests and 20 of test_q38, 12 of them pinned to one core, all passed; the queue peak there was 550,031 or more against the test's 100,000. So one test somewhere is flaky, not identified. Keep the full output of any run.

## Round 2 fixes (2026-11-03)

- Three more expert readers, on chapters 01, 07 (a1), 03, 04 (a2), 02, 09 (a3): 96 findings, all fixed, none left. One line per finding in the fix session's outcome log.
- Bugs in printed code, each with a test seen failing on the old code: chapter 01 q7, q13, q43, q56, q67, q80; chapter 02 q30, q32, q39; chapter 03 q59 (the old `var.hpp` also gave an ASan stack-buffer-overflow); chapter 09 q40 (`int(None)`); chapter 04 q34.
- 04.34: the old `spsc_split.rs` let two threads share a `Peek` of a `Cell` item. On the reader's program, 2000000 of 4000000 and a nightly ThreadSanitizer race. `Peek` now carries `PhantomData<&'a T>`, so that sharing is E0277. Test q31 reads the assembly of `write`: it was checked by mutation only (`seq_.store(s + 2)` gives an `xchg` and fails).
- Not run: 04.25 (automatic NUMA balancing) and 04.28 (the `munmap` shootdown), as this machine is one node under WSL. Their source is the ledger only, rows F44 and F45.
- Trap: `check_omcode.py` checks that a range exists, not that it ends at the end of a block. A scan for ranges that stop inside a block found `iv_matching.py`, whose listing stopped one line into `cancel`, and `iv_asof_numpy.py`, which lost its `return`. Both fixed; the other cuts it flagged (mpmc, vec.hpp, fn.hpp, aba_replay) are deliberate. A comment can also wrap in print and still pass the gate's 94 characters, as two did, so read the page.
- Orphan pass: 10 more `\enlargethispage` fixes, one stale one removed by hand before `iv_ewma.py`. Other stale ones leave small gaps, seen at printed pages 252, 259 and 263, and were left.
- Read at 130 dpi, side margins cropped, whole pages of the final build: PDF 162, 163, 165, 166, 169, 170, 177-196, 198, 199, 204, 207, 208, 210, 211, 214, 225-231, 233, 234, 257, 258, 261, 262, 264-269, 277, 278, 280, 281, 283, 284, 294, 295, 297-301, 303-305, 310-313, 318, 319, 322, 323, 326-330, 335-338, 340, 341, 344, 345, 347-349, 383-386, 389, 390. No defect. Reading many images in one request returns a placeholder instead of the image; at most 8 at a time.
- The flaky test noted above did not come back: the six whole pytest runs at the end of this round each gave 386 passed, with their output kept. It is still not identified.
