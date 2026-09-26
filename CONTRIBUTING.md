# Contributing to the One Quant Book series

Read `WRITING_A_QUANT_BOOK.md` first: it is the full procedure. This file is
the short reference a contributor keeps open while writing.

## Ground rules

- Packages, macros and environments live **only** in `styles/onequant.sty`.
- Code is never pasted into a chapter: write it under `code/`, test it, print
  an excerpt with `\omcode{path}{first}{last}{caption}` (≤ 40 lines).
- Every checkable external fact has a row in the chapter's source ledger
  (`sources/<slug>/NN-chapter.md`); volatile facts live in `dated` boxes.
- A firm is named only when the ledger holds a public source for the claim.
- New terms: `\emph{term}\index{term}` inside a `definition`, once in the
  series. `\omterm` links are generated, never hand-written.
- `` ``quotes'' `` never `"`; `\dots` never `...`; `\cref` never `\ref`.

## Environments

| Environment | Use | Label |
|---|---|---|
| `definition theorem proposition lemma corollary method example remark notation` | the lesson | `def: thm: prop: lem: cor: met: ex: rem: not:` |
| `strategyfile{Title}` with nine `\sfield{…}` | a strategy | `strat:` |
| `predictorcard{Title}` with `\sfield{…}` | a predictor | `pred:` |
| `dated{YYYY-MM}{Title}` | a volatile fact | `dat:` |
| `tutorial` + `tutsteps` inside `\section{Tutorial: …}` | guided code | `tut:` on the section |
| `build` with `\bfield{…}` inside `\section{Build: …}` | specification | `bld:` on the section |
| `exercise[$\star$]` | 8 per chapter, 3/3/2 | `exo:` first thing inside |
| `problem[{Weekend problem --- …}]` | one per chapter | `pb:` first thing inside |
| `interviewq[$\star$ \iqroles{trader, researcher}]` | 5–8 per chapter | `iq:` first thing inside |
| `omsources` | end of lesson | — |
| `solution{<key>}`; `\iqlookfor{…}` closes an interview solution | solutions file | — |

Roles for `\iqroles`: `trader, researcher, developer, mle, bank, risk`
(`risk` added 2026-09-24: Book 2 already used it for risk-manager questions,
and Book 6 needs it).

## Ledger format

```
| id | claim | source | URL | accessed | evidence | used in |
| F1 | … | … | https://… | 2026-09-18 | quote / page | dat:m1:…:… or §2 |
```
Rows start with `F<n>`. Unverifiable facts go under a heading `## EXCLUDED`.

## Interim notation (until One Quant Book 4 fixes the series notation)

| Symbol | Meaning |
|---|---|
| $b_t, a_t$ | best bid, best ask; $m_t = \tfrac12(a_t+b_t)$ mid; $s_t = a_t - b_t$ spread |
| $q$ | signed quantity (positive = long / buy) |
| $S_t$ | spot price; $F_{t,T}$ forward or futures price for delivery at $T$ |
| $r$ | financing rate (continuously compounded unless stated); $d$ dividend yield; $\ell$ borrow (stock-loan) fee |
| $\tau = T - t$ | time to expiry in years (ACT/365 unless stated) |
| $K$ | strike; $C, P$ call and put prices; $\sigma$ volatility |
| $\pnl$ | profit and loss; $\E, \Var, \Cov, \P$ as usual |
| units | `\qty{1.5}{\bp}`, `\qty{2}{\tick}`, `\money{USD}{2400000}`, latencies in `\micro\second` |

Rates, FX and credit (added for One Quant Book 2):

| Symbol | Meaning |
|---|---|
| $P(t,T)$ | discount factor (price at $t$ of 1 paid at $T$); $P(T) = P(0,T)$ |
| $\delta$, $\delta_i$ | accrual (day-count) fraction of a period |
| $y$ | yield to maturity; $c$ coupon rate (bond coupon, or a CDS standard coupon) |
| $F(t;T_1,T_2)$ | simple forward rate for $[T_1,T_2]$ seen at $t$; $f(t,T)$ instantaneous forward |
| $D$, $D_{\mathrm{mod}}$, $\mathrm{DV01}$ | Macaulay and modified duration; value of one basis point (currency, positive for a long bond) |
| $\mathcal{C}$ | convexity |
| $r_{\mathrm{on}}$ | overnight benchmark rate; $K$ fixed rate of a swap (as a strike) |
| $S$, $F$ | FX spot and outright forward, in units of the **quote** currency per one unit of the **base** currency (pair written `EURUSD`); $r_d$, $r_f$ domestic (quote) and foreign (base) rates |
| $\lambda$ | hazard rate; $R$ recovery rate; $\mathcal{S}$ a credit spread (CDS par spread, bond Z-spread $z$) — never $s$, which is the bid–ask spread |

## Series notation (fixed in One Quant Book 4, chapter 1)

Agreed at the Books 3–6 batch sync (2026-09-24). Books 4, 5 and 6 and every
later book follow it; Book 4 ch. 1 prints it. It **extends** the interim tables
above, whose meanings are kept ($s_t$ bid–ask spread, $\mathcal S$ credit
spread, $\lambda$ an intensity or hazard rate, $\tau = T-t$, $r$ a rate, $\ell$
borrow fee, $K$ strike, $P(t,T)$ discount factor, $y$ yield, $\delta$ accrual,
$R$ recovery). A symbol marked *local* may be reused with another meaning in a
chapter that declares it.

**Probability and measures**

| Symbol | Meaning |
|---|---|
| $(\Omega,\mathcal F,\mathbb P)$, $\mathbb F=(\mathcal F_t)$ | probability space, filtration (usual conditions) |
| $\E_t[X]=\E[X\mid\mathcal F_t]$, $\E^{\mathbb Q}_t$ | conditional expectation; under another measure |
| $\mathbb P$, $\mathbb Q$ | real-world measure; risk-neutral measure (numeraire $B_t$) |
| $B_t=\exp\int_0^t r_s\,ds$ | money-market (bank) account; $r_t$ the short rate, always time-indexed in model chapters |
| $\mathcal N_t$, $\mathbb Q^{\mathcal N}$ | a generic numeraire and its measure ($N_t$ is reserved for counting processes) |
| $\mathbb Q^T$, $\mathbb Q^A$ ($\mathbb Q^{a,b}$) | $T$-forward measure (numeraire $P(t,T)$); annuity measure (numeraire $A_t$ / $A_{a,b}(t)$); $\mathbb Q^d$ spot measure |
| $d\mathbb Q/d\mathbb P$, $Z_t$ | Radon–Nikodym derivative; density process |
| $\Phi$, $\varphi$ | standard normal cdf and pdf (never $N(d_1)$); $\mathcal N(m,s^2)$ the normal law, always with arguments |
| $\varphi_X(u)=\E[e^{iuX}]$ | characteristic function, always subscripted |
| $\mathbf 1_A$; $\overset{d}{=}$, $\xrightarrow{d}$, $\xrightarrow{\mathbb P}$ | indicator; equality and convergence in law, in probability |
| $\tau$ (unsubscripted, stopping-time chapters) | a stopping time; where it meets a time to expiry, write $T-t$. Default times are always subscripted: $\tau_C$ (counterparty), $\tau_B$ (bank) |

**Stochastic calculus and processes**

| Symbol | Meaning |
|---|---|
| $W_t$; $W^{\mathbb Q}_t$, $W^T_t$ | Brownian motion under the measure in force; decorated when two measures appear; $d\langle W^i,W^j\rangle_t=\rho_{ij}\,dt$ |
| $[X]_t$, $[X,Y]_t$ | quadratic variation, covariation ($\langle\cdot\rangle$ only for the predictable version); $\mathcal E(X)_t$ stochastic exponential |
| $dX=\mu(t,X)\,dt+\sigma(t,X)\,dW$ | SDE; $\mathcal L$ the generator ($\mathcal L f=\mu f'+\tfrac12\sigma^2 f''$), $\mathcal L^*$ its adjoint |
| $dX=\kappa(\bar x-X)\,dt+\sigma\,dW$ | Ornstein–Uhlenbeck; $\kappa$ speed of mean reversion, half-life $\ln 2/\kappa$ |
| $dv=\kappa(\bar v-v)\,dt+\eta\sqrt v\,dW$ | square-root process; Feller condition $2\kappa\bar v\ge\eta^2$. Heston is $(v_0,\kappa,\bar v,\eta,\rho)$: $\eta$ is **the vol-of-vol throughout the series** |
| $N_t$, $t_1<t_2<\dots$ | counting process and event times |
| $\lambda_t$ | intensity of a point process: Poisson rate, hazard rate, **Hawkes conditional intensity** $\lambda_t=\mu+\sum_{t_i<t}g(t-t_i)$ (baseline $\mu$ *local*, kernel $g$, exponential $g(u)=\alpha e^{-\beta u}$ *local*, branching ratio $\lVert g\rVert_1$, multivariate $\lambda^{(i)}_t$, branching matrix $G$, stable iff spectral radius $<1$) |
| $\Lambda_t=\int_0^t\lambda_s\,ds$, $M_t=N_t-\Lambda_t$ | compensator (cumulative hazard in credit); compensated martingale ($M_t$ *local*) |
| $(\sigma^2,\nu,\gamma)$, $\nu(dx)$, $\psi$ | Lévy triplet (Cont–Tankov order), Lévy measure, characteristic exponent $\varphi_{X_t}(u)=e^{t\psi(u)}$ |
| $H$ | Hurst exponent (fractional Brownian motion $W^H_t$) |

**Statistics and time series**

| Symbol | Meaning |
|---|---|
| $n$, $\theta\in\Theta$, $\theta_0$ | sample size, parameter, true value; hat = estimate, tilde = alternative or shrunk estimate, bar = sample mean |
| $\ell_n(\theta)$, $\mathcal I(\theta)$ | log-likelihood (always with subscript and argument; bare $\ell$ is the borrow fee); Fisher information |
| $V=A^{-1}BA^{-1}$ | sandwich asymptotic variance *local*; $\mathrm{se}(\hat\theta)$ standard error |
| $\mathrm{SR}$, $\widehat{\mathrm{SR}}$ | Sharpe ratio and its estimate |
| $R_t=\ln(S_t/S_{t-1})$ | log return; $R$ without subscript stays the recovery rate |
| $L$ (lag), $\Delta=1-L$ | lag and difference operators (time-series chapters; *local*) |
| $\gamma(h)$, $\rho(h)$ | autocovariance, autocorrelation; AR/MA coefficients $\phi_i$, $\vartheta_j$ always indexed; innovations $\varepsilon_t$ |
| $\mathrm{RV}_t$, $\mathrm{IV}_t$ | realised and integrated variance; implied volatility is therefore $\sigma_{\mathrm{imp}}$, never ``IV'' in a formula |
| $x_{t\mid t}$, $\Sigma_{t\mid t}$, $K_t$ | Kalman estimate, covariance, gain (state-space chapters, bold vectors) |

**Matrices, optimisation, numerics**

| Symbol | Meaning |
|---|---|
| $\Sigma$, $C$, $\hat\Sigma$ | covariance, correlation, sample covariance; vectors are columns, $\mathbf 1$ ones vector, $I_n$ identity, ${}^\top$ transpose |
| $\lambda_i$ (always indexed) | eigenvalues $\lambda_1\ge\dots\ge\lambda_N$; eigenvectors $v_i$; $\operatorname{cond}(A)$ condition number (not $\kappa$) |
| $\min f(x)$ s.t. $g_i(x)\le0$, $h_j(x)=0$ | optimisation; multipliers $u\ge0$, $v$ (not $\lambda$); $x^\star$, $p^\star$, $d^\star$ |
| $\mathrm{fl}(x)$, $u=2^{-53}$, $\varepsilon_{\mathrm{mach}}=2^{-52}$ | floating point (binary64, round to nearest); $\mathrm{ulp}(x)$ |
| $t_k=k\Delta t$, $x_j$, $V^k_j$ | time grid, space grid, numerical solution; $M$ Monte Carlo paths, estimator $\hat V_M$ |

**Options and volatility**

| Symbol | Meaning |
|---|---|
| $\sigma_{\mathrm{imp}}(K,T)$ | implied volatility |
| $k=\ln(K/F_{0,T})$ | log-moneyness (forward-based) |
| $w(k,T)=\sigma_{\mathrm{imp}}^2T$, $\theta_T$ | total implied variance; ATM total variance |
| $\sigma_{\mathrm{loc}}(t,S)$, $v_t$, $\xi_t(u)=\E^{\mathbb Q}_t[v_u]$ | local volatility; instantaneous variance; forward variance curve |
| $\Delta,\Gamma,\mathcal V,\Theta$; $\mathrm{Vanna}$, $\mathrm{Volga}$, $\mathrm{Rho}$ | Greeks ($\rho$ is **always** a correlation, so the rate Greek is upright Rho); cash gamma $\tfrac12\Gamma S^2$; bucketed sensitivity $\Delta_k$ |
| $H$ (with $K$) | barrier level; $g(\cdot)$ a payoff |
| $(\alpha,\beta,\rho,\nu)$, $\zeta$ | SABR parameters; shift of shifted SABR / shifted lognormal |
| $(a,b,\rho,m,\varsigma)$ | raw SVI |
| $\mu_J$, $\sigma_J$ | mean and volatility of the log-jump size |
| $L(t,S)$ | leverage function of a stochastic-local-volatility model (always with arguments) |
| $D_i$ at $t_i$ | cash dividends |

**Rates, credit, XVA and risk**

| Symbol | Meaning |
|---|---|
| $f(t,T)$, $\sigma_f(t,T)$ | instantaneous forward rate and its volatility (HJM) |
| $F_k(t)=F(t;T_{k-1},T_k)$, $\sigma_k(t)$, $\rho_{ij}$ | market-model forwards, volatilities, correlations; tenor dates $T_0<\dots<T_n$ |
| $S_{a,b}(t)$, $A_{a,b}(t)$ | swap rate and annuity |
| $Q_C(t)$ | survival probability of name $C$ (italic, distinct from $\mathbb Q$); $\mathrm{PD}$, $\mathrm{LGD}=1-R$, $\mathrm{CS01}$, $\mathrm{JTD}$ |
| $C^{\mathrm{Ga}}_\Sigma$, $C^t_{\nu,\Sigma}$ | Gaussian and Student-$t$ copulas (always decorated); one-factor $X_i=\sqrt\rho Z+\sqrt{1-\rho}\,\varepsilon_i$ |
| $V_t$, $M_t$, $M^{\mathrm{VM}}_t$, $M^{\mathrm{IM}}_t$ | netting-set value; collateral (not $C_t$, a call price); $\mathrm{Th}$ threshold, $\mathrm{MTA}$ minimum transfer amount |
| $\mathrm{EE}(t)$, $\mathrm{ENE}(t)$, $\mathrm{EPE}$, $\mathrm{PFE}_\alpha(t)$ | exposure profiles |
| CVA, DVA, FVA, MVA, KVA | upright; funding spread $\mathcal S_F$ |
| $L=-\Delta V$ | loss (positive = loss); $\mathrm{VaR}_{\alpha,h}$, $\mathrm{ES}_{\alpha,h}$, confidence $\alpha$, horizon $h$ days |
| $\mathrm{RW}_k$, $\mathrm{WS}_k$, $\rho_{kl}$, $\gamma_{bc}$ | FRTB / SIMM risk weights, weighted sensitivities, correlations |
| $I(t)$, $P_N$, $P_R$ | inflation index; nominal and real discount factors |

**Commodities and crypto** (Book 3)

| Symbol | Meaning |
|---|---|
| $F_{t,T}=S_te^{(r+u-y_c)\tau}$ | $y_c$ convenience yield, $u$ proportional storage cost |
| $\theta_i$, $\mathrm{HDD}$, $\mathrm{CDD}$ | daily temperature (*local*), degree days |
| $p_h$, $p_n$ | power price in market time unit $h$; nodal price |
| $P^{\mathrm{idx}}_t$, $P^{\mathrm{mark}}_t$, $\pi_t$, $\phi$ | perpetual index and mark price, premium index, funding rate per interval (*local*) |
| $x,y,L,p=y/x$ | AMM reserves, liquidity, pool price (*local* to the DeFi chapters) |

## Books 10–13 additions (sync, 2026-09-25)

Series symbols above keep their meaning. *Local* symbols are declared at first use in the chapter
that uses them and never leave it.

| symbol | meaning |
|---|---|
| $P^\ast_t$ | efficient (fundamental) price, Books 10–13 (not $v_t$, the variance, nor $V_t$, a value); $\hat P_t$ a fair-price estimate (B11) |
| $Q^b_t, Q^a_t$ | size at the best bid and ask queues; $n$ orders ahead of one's own (local) |
| $\delta_{\mathrm{tick}}$ | tick size (always decorated; bare $\delta$ stays the accrual fraction; $\delta^b_t,\delta^a_t$ are quote depths in B11's inventory chapters, local) |
| $\epsilon_n\in\{\pm1\}$ | trade sign (as Book 1 ch. 10), distinct from innovations $\varepsilon_t$; propagator kernel $G(\ell)$, response function $\mathcal R(\ell)$ |
| $\Delta t^{\mathrm{md}}, \Delta t^{\mathrm{oe}}, \Delta t^{\mathrm{rt}}$ | market-data, order-entry and round-trip latency (Books 10–13); stage latencies $X_i$ and percentiles $q_p(X)$ local to Book 13, p50/p99/p99.9 in prose |
| $f^{\mathrm{make}}, f^{\mathrm{take}}$ | maker and taker fee per unit traded, negative for a rebate |
| $q_t$, $\bar q$ | inventory and its bound (B11); parent size $X$, holdings $x_t$, trading rate $v_t=-\dot x_t$, participation $\pi_t$ local to B10's execution chapters |
| $\eta$ | stays the vol-of-vol, **except** as a declared local symbol for the Almgren–Chriss temporary-impact coefficient (B10 ch. 14–16, 28, as in the literature) and the learning rate (B12); neither chapter uses a vol-of-vol. The square-root law's prefactor is $Y$: $I(Q)=Y\sigma_d\sqrt{Q/V_d}$ |
| $\gamma$ | risk aversion in execution and market-making models (local; $\gamma(h)$ with an argument stays the autocovariance) |
| $\lambda$ | stays an intensity; Kyle's $\lambda$ inside the Kyle sections only, $\lambda_{\mathrm K}$ elsewhere |
| $\rho=\lambda/\mu$ | utilisation of a queue, local to Book 13 (as Book 4 ch. 8); $\rho$ is otherwise a correlation |
| $\ell(y,\hat y)$, $\mathcal L_n(\theta)$ | per-observation loss (always two arguments) and empirical loss (always subscripted), B12 |
| $x_t, u_t, g_{t+1}, G_t, \pi(u\mid x), V^\pi, Q^\pi$ | RL state, action, reward, return, policy, value functions (B12 ch. 17–18; avoids $s_t$ spread and $a_t$ ask) |
| units | prices in code as integers of 1/10,000 currency unit; time as integer ns since midnight; `\qty{}{\nano\second}`, `\micro\second`, `\giga\hertz`, `\byte` |

## Gates

`tools/gates.sh chapter <slug>/<NN-chapter>`, `make test-code CH=<slug>/<NN-chapter>`,
`latexmk && tools/gates.sh log`, then render and read every figure
(`tools/figpage.sh "<caption words>"`).

## Code naming

- Chapter modules live in `code/<slug>/NN-chapter/python/` and must have a
  name unique in the book (tests of all chapters run in one pytest session).
- Running-project modules live in `code/firm/<component>/firm_<component>.py`
  (the `firm_` prefix keeps them from colliding with a chapter's teaching
  module of the same name); their acceptance tests in `…/tests/`.
- Chart scripts are `fig_*.py`; they write only under `figdata/`.
