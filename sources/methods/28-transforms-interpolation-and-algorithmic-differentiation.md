# 28. Transforms, Interpolation and Algorithmic Differentiation — brief and source ledger

## Brief

- **Hook.** The risk run bumps 400 curve points one at a time and reprices the book 401 times every night. The same sensitivities come out of one adjoint sweep that costs about as much as four prices.
- **Sections.** Fourier methods; Interpolation and splines; Root finding; Forward and adjoint algorithmic differentiation.
- **Defines.** discrete Fourier transform, fast Fourier transform, COS method, cubic spline, natural cubic spline, monotone cubic interpolation, Runge phenomenon, bisection method, secant method, Brent's method, algorithmic differentiation, forward mode, reverse mode, adjoint mode, dual number, tape, checkpointing.
- **Uses (defined earlier).** characteristic function, characteristic exponent, Lévy process, Newton's method, condition number, implied volatility, zero-coupon rate, Monte Carlo method, tridiagonal matrix algorithm.
- **Results (named theorems, not terms).** Fourier inversion (Gil-Pelaez) formula; exponential convergence of the COS method for smooth densities; a natural cubic spline minimises the integrated squared second derivative; Fritsch-Carlson condition for monotone Hermite interpolation; convergence of bisection, secant and Brent; cheap gradient principle: the reverse sweep costs a small constant multiple of one evaluation.
- **Tutorial.** Price by the COS method from a Lévy characteristic function of `firm.levy` and check against Monte Carlo; interpolate zero rates with natural and monotone splines and compare the forward curves; compute 400 sensitivities of a toy portfolio by bumping, forward mode and reverse mode, and time them.
- **Build.** `firm.aad`: tape-based reverse-mode and dual-number forward-mode differentiation (operator overloading in C++20, a Rust twin, a Python reference), with checkpointing and a gradient check against bumping; later books' pricing library and risk engine use it.
- **Weekend problem.** One sweep instead of 401 — named result: the measured ratio of the cost of the adjoint gradient to one evaluation for a 400-input portfolio function, against 401 for bumping, and the agreement between the two.
- **Facts to verify.** Cooley and Tukey 1965 (Mathematics of Computation); Fang and Oosterlee 2008 (SIAM J. Scientific Computing) COS method; Gil-Pelaez 1951 (Biometrika); Carr and Madan 1999 (J. Computational Finance), mentioned only; Fritsch and Carlson 1980 (SIAM J. Numerical Analysis); Hagan and West 2006 (Applied Mathematical Finance), mentioned; Brent 1973, Algorithms for Minimization without Derivatives; Wengert 1964 (Comm. ACM); Linnainmaa 1970/1976; Griewank and Walther 2008, Evaluating Derivatives; Giles and Glasserman 2006 (Risk) 'Smoking adjoints'; Runge 1901.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | J. W. Cooley and J. W. Tukey, "An algorithm for the machine calculation of complex Fourier series", Mathematics of Computation 19(90) (1965), 297-301 | Crossref record | https://doi.org/10.1090/S0025-5718-1965-0178586-1 | 2026-09-24 | vol 19(90), pp 297-301 | def FFT; omsources |
| F2 | F. Fang and C. W. Oosterlee, "A novel pricing method for European options based on Fourier-cosine series expansions", SIAM J. Sci. Comput. 31(2) (2008), 826-848 | Crossref record | https://doi.org/10.1137/080718061 | 2026-09-24 | vol 31(2), pp 826-848 | def COS; proposition; omsources |
| F3 | J. Gil-Pelaez, "Note on the inversion theorem", Biometrika 38(3-4) (1951), 481-482 | Crossref record | https://doi.org/10.1093/biomet/38.3-4.481 | 2026-09-24 | vol 38(3-4), pp 481-482 | proposition (Fourier inversion); omsources |
| F4 | P. Carr and D. Madan, "Option valuation using the fast Fourier transform", J. Computational Finance 2(4) (1999), 61-73 | Crossref record | https://doi.org/10.21314/JCF.1999.043 | 2026-09-24 | vol 2(4), pp 61-73 | section 1 (mention); omsources |
| F5 | F. N. Fritsch and R. E. Carlson, "Monotone piecewise cubic interpolation", SIAM J. Numer. Anal. 17(2) (1980), 238-246 | Crossref record | https://doi.org/10.1137/0717021 | 2026-09-24 | vol 17(2), pp 238-246 | proposition (Fritsch-Carlson); omsources |
| F6 | P. S. Hagan and G. West, "Interpolation methods for curve construction", Applied Mathematical Finance 13(2) (2006), 89-129 | Crossref record | https://doi.org/10.1080/13504860500396032 | 2026-09-24 | vol 13(2), pp 89-129 | section 2 (mention); omsources |
| F7 | C. Runge, "Uber empirische Funktionen und die Interpolation zwischen aquidistanten Ordinaten", Zeitschrift fur Mathematik und Physik 46 (1901), 224-243 | Wikipedia "Runge's phenomenon" (reference list) | https://en.wikipedia.org/wiki/Runge%27s_phenomenon | 2026-09-24 | citation "Zeitschrift fur Mathematik und Physik, 46: 224-243" | def Runge phenomenon; omsources |
| F8 | R. P. Brent, Algorithms for Minimization without Derivatives, Prentice-Hall, Englewood Cliffs, 1973; chapter 4: zero finder combining interpolation and bisection that never converges much more slowly than bisection | author's publication page and abstract | https://maths-people.anu.edu.au/~brent/pub/pub011.html | 2026-09-24 | Prentice-Hall 1973; abstract (rpb011a.pdf): "never converges much more slowly than bisection" | def Brent's method; proposition; omsources |
| F9 | R. E. Wengert, "A simple automatic derivative evaluation program", Comm. ACM 7(8) (1964), 463-464 | Crossref record | https://doi.org/10.1145/355586.364791 | 2026-09-24 | vol 7(8), pp 463-464 | def forward mode; omsources |
| F10 | S. Linnainmaa, "Taylor expansion of the accumulated rounding error", BIT 16(2) (1976), 146-160 | Crossref record | https://doi.org/10.1007/BF01931367 | 2026-09-24 | vol 16(2), pp 146-160 | def reverse mode; omsources |
| F11 | A. Griewank and A. Walther, Evaluating Derivatives, 2nd ed., SIAM, 2008 (cheap gradient principle) | Crossref record | https://doi.org/10.1137/1.9780898717761 | 2026-09-24 | SIAM, 2008 | proposition (cheap gradient); omsources |
| F12 | M. Giles and P. Glasserman, "Smoking adjoints: fast Monte Carlo Greeks", Risk, January 2006 | Risk.net article page; author's PDF | https://www.risk.net/derivatives/interest-rate-derivatives/1500261/smoking-adjoints-fast-monte-carlo-greeks | 2026-09-24 | title and authors; Glasserman's page hosts RiskJan2006.pdf | section 4; omsources |
| F13 | Treasury constant-maturity yields on 3 July 2023: 1M 5.27, 3M 5.44, 6M 5.53, 1Y 5.43, 2Y 4.94, 3Y 4.56, 5Y 4.19, 7Y 4.03, 10Y 3.86, 20Y 4.08, 30Y 3.87 percent | FRED (Board of Governors, H.15), series DGS1MO ... DGS30 | https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10&cosd=2023-07-03&coed=2023-07-03 | 2026-09-24 | values as downloaded to data/methods/ust_curve_2023-07-03.csv | section 2; figure |
| F14 | A. Griewank, "Who invented the reverse mode of differentiation?", Documenta Mathematica, Extra Volume ISMP (2012), 389-400: Linnainmaa (Lin76) had the idea in 1970 and used it to estimate rounding errors; he finished his master's thesis on the estimation of rounding errors in 1970; the reversal technique was suggested by several people since the late 1960s | the article (EMIS PDF) | https://www.emis.de/journals/DMJDMV/vol-ismp/52_griewank-andreas-b.html | 2026-09-24 | "the idea came to him on a sunny afternoon in a Copenhagen park in 1970"; "After finishing his Master Thesis concerning the Estimation of Rounding Errors in 1970"; "suggested by several people from various fields since the late 1960s" | section 4; omsources |

## EXCLUDED

- Linnainmaa's 1970 master's thesis: restored in Phase C through Griewank (2012), row F14; the text does not call it the first description, since Griewank reports earlier and independent discoveries.
- A precise constant for the cheap gradient principle is not quoted from Griewank-Walther (not accessible); the chapter proves the bound 5 for its own operation count and cites the book for the principle.

## Brief deviations

- The measured cost ratio is an operation count (deterministic, tested: 3.58); wall-clock is only bounded (C++ test asserts below 20; runs gave 5 to 7), since timings are not reproducible.
- Yields are treated as zero rates for the interpolation illustration (stated in the text).
