# 9. Native Extensions — brief and source ledger

## Brief

- **Hook.** A C++ function called from Python a million times, once per tick, was slower than the numpy version it replaced; called once on the whole array, it was eight times faster. Everything about a native extension is decided at the boundary.
- **Sections.** Why and when to leave Python; The boundary: calls, types and the interpreter lock; Binding C++ with a header-only binder; Binding Rust through the C ABI; Zero-copy across the boundary.
- **Defines.** native extension, foreign function interface, application binary interface, buffer protocol, zero-copy transfer, language binding, boundary-crossing cost.
- **Uses (defined earlier).** interpreter overhead (ch8), global interpreter lock (ch8), array programming (ch8), zero-cost abstraction (B13.9), undefined behaviour (B13.8), data race (B13.9), as-of join (B7.3), EWMA volatility (B4.18).
- **Tutorial.** Implement one kernel -- a streaming as-of lookup and an EWMA over tick arrays -- four times: pure Python, numpy, a C++20 pybind11 module taking numpy arrays by buffer without copying and releasing the interpreter lock, and a Rust cdylib exposing extern C functions called through ctypes on numpy pointers; test all four against each other, then time per-call overhead and throughput against array size. End state: a chart of time against array size for the four, with the break-even size marked.
- **Build.** `firm.natext`: the kernel in C++20 (pybind11 module built with g++ and python3-config), in Rust (cdylib, no external crates, C ABI, a ctypes loader with argument types declared), the Python and numpy references, and the parity and ownership tests (read-only views, lengths checked, no aliasing writes); PyO3 described with a cited source, not built.
- **Weekend problem.** The million calls -- named result: the per-call boundary cost of each binding, the array size above which each native version beats numpy, and the day's saving of moving the loop, not the body, across the boundary.
- **Facts to verify.** pybind11 documentation: numpy arrays, buffer protocol, gil_scoped_release; Python buffer protocol (PEP 3118); ctypes documentation; Rust reference: extern "C" functions and cdylib crate type; PyO3 user guide (described only).
- **Data.** Synthetic tick arrays; measured on this laptop.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | pybind11 NumPy support: the buffer protocol gives access to data without copying; array_t c_style enforces row-major layout; forcecast converts non-conforming arguments into conforming arrays; noconvert() accepts only exact types and raises otherwise | pybind11 documentation, NumPy | https://pybind11.readthedocs.io/en/stable/advanced/pycpp/numpy.html | 2026-09-28 | "It is even possible to completely avoid copy operations"; forcecast "automatically converting non-conforming arguments into arrays meeting the specified requirements"; noconvert: "only exact type matches are accepted" | sections 3-4; omsources |
| F2 | PEP 3118, Revising the buffer protocol, status Final: lets objects share internal memory without copying | Python Enhancement Proposals | https://peps.python.org/pep-3118/ | 2026-09-28 | "PEP 3118 - Revising the buffer protocol"; "Status: Final" | section 3; omsources |
| F3 | PyO3: "Rust bindings for Python, including tools for creating native Python extension modules" | PyO3 user guide | https://pyo3.rs/main/ | 2026-09-28 | "Rust bindings for Python, including tools for creating native Python extension modules." | dat:pl:native-extensions:pyo3 |
| F4 | Rust Reference: crate-type cdylib produces a dynamic system library used when compiling a dynamic library to be loaded from another language (.so on Linux) | The Rust Reference, Linkage | https://doc.rust-lang.org/reference/linkage.html | 2026-09-28 | "A dynamic system library will be produced. This is used when compiling a dynamic library to be loaded from another language." | dat:pl:native-extensions:pyo3; omsources |

## EXCLUDED

- ctypes documentation (brief): mechanism only; not cited separately.

