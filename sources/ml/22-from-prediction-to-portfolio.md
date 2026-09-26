# 22. From Prediction to Portfolio — brief and source ledger

## Brief

- **Hook.** The model with the lowest forecast error of the quarter produced the worst portfolio after costs: it was most accurate on the stocks nobody could trade, and least on the ones the optimiser bet on.
- **Sections.** Why the forecast loss is not the trading loss; Losses aligned with profit and loss; Parametric portfolio policies; Learning through the optimiser; When end-to-end learning overfits.
- **Defines.** predict-then-optimise, decision-focused learning, differentiable optimisation layer, parametric portfolio policy.
- **Uses (defined earlier).** mean--variance optimisation (B7.25), turnover penalty (B7.25), cost-aware optimisation (B7.27), transfer coefficient (B7.15), fundamental law of active management (B7.15), breadth (B7.15), quadratic programme (B4.23), Karush--Kuhn--Tucker conditions (B4.23), certainty equivalent (B4.9), baseline model (ch4), multilayer perceptron (ch7), Adam (ch7), early stopping (ch5), stochastic gradient descent (B4.24), reverse mode (B4.28), prediction target (B7.6), forecast horizon (B7.6), information coefficient (B7.6), in-sample (B7.20), out-of-sample (B7.20), cross-validation (B4.16).
- **Tutorial.** On a firm.synthmkt panel with trading costs from firm.tcost, compare an MSE-trained network fed to a mean-variance optimiser with the same network trained through a differentiable mean-variance layer with costs, and with a parametric portfolio policy on characteristics; report gross and net Sharpe ratios, turnover and their spread across seeds. Data: synthetic.
- **Build.** `firm.e2eport`: a differentiable mean-variance layer with costs (closed form and unrolled projected gradient, checked against firm.portcons), utility and Sharpe-ratio losses, parametric portfolio policies, and the evaluation harness against predict-then-optimise; Python on PyTorch.
- **Weekend problem.** The loss that pays -- named result: the net Sharpe ratio of predict-then-optimise against decision-focused learning and the parametric policy, with the gap's spread over seeds.
- **Facts to verify.** Brandt, Santa-Clara and Valkanov 2009 parametric portfolio policies (RFS); Elmachtoub and Grigas 2022 smart predict, then optimize (Management Science); Donti, Amos and Kolter 2017 task-based end-to-end model learning (NeurIPS); Amos and Kolter 2017 OptNet (ICML); Agrawal et al. 2019 differentiable convex optimization layers (NeurIPS); Butler and Kwon 2023 integrating prediction in mean-variance portfolio optimization (Quantitative Finance); Zhang, Zohren and Roberts 2020 deep learning for portfolio optimisation (JFDS).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | M. W. Brandt, P. Santa-Clara, R. Valkanov, "Parametric portfolio policies", Review of Financial Studies 22(9) 2009: weights modelled directly as a function of characteristics, coefficients found by optimising the investor's average utility | Crossref/OpenAlex record | https://doi.org/10.1093/rfs/hhp003 | 2026-09-26 | abstract: "We model directly the portfolio weight in each asset as a function of the asset's characteristics. The coefficients of this function are found by optimizing the investor's average utility" | def. parametric portfolio policy; omsources |
| F2 | A. N. Elmachtoub, P. Grigas, "Smart 'predict, then optimize'", Management Science 68(1) 2022 (online 2021) | Crossref/OpenAlex record | https://doi.org/10.1287/mnsc.2020.3922 | 2026-09-26 | title, journal as registered | sec. forecast loss; omsources |
| F3 | P. L. Donti, B. Amos, J. Z. Kolter, "Task-based end-to-end model learning in stochastic optimization", arXiv:1703.04529 2017 | arXiv API | https://arxiv.org/abs/1703.04529 | 2026-09-26 | title and abstract | def. decision-focused learning; omsources |
| F4 | B. Amos, J. Z. Kolter, "OptNet: differentiable optimization as a layer in neural networks", arXiv:1703.00443 2017 | arXiv API | https://arxiv.org/abs/1703.00443 | 2026-09-26 | title and abstract | def. differentiable optimisation layer; iq 6; omsources |
| F5 | A. Agrawal et al., "Differentiable convex optimization layers", arXiv:1910.12430 2019 | arXiv API | https://arxiv.org/abs/1910.12430 | 2026-09-26 | title and abstract | def. differentiable optimisation layer; omsources |
| F6 | A. Butler, R. H. Kwon, "Integrating prediction in mean-variance portfolio optimization", Quantitative Finance 23(3) 2023 | Crossref/OpenAlex record | https://doi.org/10.1080/14697688.2022.2162432 | 2026-09-26 | title, journal as registered | omsources |

## EXCLUDED

- Every Sharpe ratio, coefficient, error and turnover is the chapter's synthetic panel (firm.e2eport), tested in code/ml/22-from-prediction-to-portfolio/tests/test_solutions.py.
- Zhang, Zohren and Roberts 2020 (deep learning for portfolio optimisation, JFDS): planned, not cited.
- The brief's firm.synthmkt panel with firm.tcost costs: replaced by a two-universe characteristics panel with a linear cost, so that the forecast is misspecified by design and the true coefficients are known.
