# 8. C++ for Latency III: The Compiler — brief and source ledger

## Brief

- **Hook.** In 2009 a null-pointer check vanished from a Linux kernel driver: the pointer had been dereferenced one line earlier, so the compiler concluded it could not be null. Undefined behaviour is a contract, and the optimiser reads it literally.
- **Sections.** Undefined behaviour as an optimisation contract; Aliasing; Flags and target selection; Profile-guided and link-time optimisation; Reading assembly.
- **Defines.** undefined behaviour, strict aliasing, profile-guided optimisation, link-time optimisation, function multiversioning.
- **Uses (defined earlier).** inlining (ch7), compiler barrier (ch2), microbenchmark (ch2), fused multiply-add (B4.25), bitwise reproducibility (B4.25).
- **Tutorial.** Build the feed decoder at -O0, -O2, -O3, -O3 -march=native, with profile-guided and with link-time optimisation under g++ 11; check that every build decodes the sample to the same bytes; read the hot loop in the disassembly; show a signed-overflow assumption removing a check, and the undefined-behaviour sanitiser catching it; show -ffast-math changing a result. End state: a table of speed-ups over -O2 and the one flag that changed an answer.
- **Build.** `firm.flagbench`: a driver that compiles a benchmark under a matrix of flag sets, verifies identical outputs, measures, and ranks; Python driving g++ and cargo. The firm's release flags are chosen with it.
- **Weekend problem.** The fast build that was wrong -- named result: the speed-up of profile-guided plus link-time plus target-specific optimisation over -O2 on the decoder, and the output difference -ffast-math introduced.
- **Data.** Measured on this laptop only; generated assembly committed with the compiler version named.
- **Facts to verify.** Linux kernel tun driver null-check removal, CVE-2009-1897 (LWN coverage, 2009); ISO C++ definition of undefined behaviour ([defns.undefined]); GCC 11 manual: -O levels, -fprofile-generate/-fprofile-use, -flto, -march, -ffast-math, target_clones; Lattner 2011, What every C programmer should know about undefined behavior (LLVM blog).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Linux 2.6.30 tun driver: `struct sock *sk = tun->sk;` then `if (!tun) return POLLERR;` -- GCC removed the NULL test because the pointer had already been dereferenced; exploitable when NULL was a mapped address (CVE-2009-1897) | J. Corbet, Fun with NULL pointers, part 1, LWN.net, 20 July 2009 | https://lwn.net/Articles/342330/ | 2026-09-25 | code snippet as quoted; the compiler reasoned the pointer "cannot be NULL. So there is no point in checking it" | hook, section 1 |
| F2 | "knowing that INT_MAX+1 is undefined allows optimizing X+1 > X to true" | C. Lattner, What Every C Programmer Should Know About Undefined Behavior #1/3, LLVM blog, 13 May 2011 | https://blog.llvm.org/2011/05/what-every-c-programmer-should-know.html | 2026-09-25 | quote as given | section 1 |
| F3 | GCC 11.4: -fstrict-aliasing assumes an object of one type never resides at the same address as an object of a different type (unsigned int may alias int; a character type may alias anything), enabled at -O2, -O3, -Os; -flto writes GIMPLE into the object files and optimises all function bodies at link time as if in one translation unit; -fprofile-use enables feedback-directed optimisations (branch probabilities, value profiling, unrolling, peeling, inlining, vectorisation, function reordering); -ffast-math is enabled by no -O option except -Ofast since it can result in incorrect output for programs that depend on exact IEEE rules | GCC 11.4 manual, Optimize Options | https://gcc.gnu.org/onlinedocs/gcc-11.4.0/gcc/Optimize-Options.html | 2026-09-25 | "an object of one type is assumed never to reside at the same address as an object of a different type"; "as if they had been part of the same translation unit"; "can result in incorrect output" | sections 2-4 |
| F4 | GCC target_clones attribute: clones a function into versions compiled for different targets (e.g. sse4.1 and avx) with dispatch at run time | GCC 11.4 manual, Common Function Attributes | https://gcc.gnu.org/onlinedocs/gcc-11.4.0/gcc/Common-Function-Attributes.html | 2026-09-25 | "The target_clones attribute is used to specify that a function be cloned into multiple versions compiled with different target options" | section 3 |

## EXCLUDED

