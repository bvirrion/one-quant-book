# Glossary — One Quant Book 6 (`rates-credit-risk`) in French

Written by the coordinator (claude-opus-5-5) on 2026-11-11; same rules as `GLOSSARY_BOOK_1_FR.md`. This file lists
Book 6's own defined terms; the run uses `GLOSSARY_BOOK_6_FR.run.md`, which adds every earlier book's lines as `00`.
Rates, XVA and risk desks in Paris keep the product and adjustment acronyms in English (CMS, CVA, FVA, VaR, CS01) and
most model names; regulatory notions take the French of the EU texts (exigence de fonds propres, portefeuille de
négociation, ratio de liquidité à court terme).

01 | pillar / pillars | pilier / piliers [a node of a curve]
01 | instantaneous forward rate | taux forward instantané
01 | Curve calibration / curve calibration | calibration de la courbe
01 | Flat-forward interpolation / flat-forward interpolation | interpolation à forward constant
01 | Monotone convex interpolation / monotone convex interpolation | interpolation monotone convexe
01 | Nelson--Siegel curve | courbe de Nelson--Siegel
01 | interpolation locality | localité de l'interpolation
02 | tenor basis swap | swap de base de ténor (tenor basis swap)
02 | tenor basis | base de ténor
02 | discount curve | courbe d'actualisation
02 | projection curve | courbe de projection
02 | multi-curve framework | cadre multi-courbes
02 | collateral rate | taux de rémunération du collatéral
02 | CSA discounting | actualisation CSA
02 | Price alignment interest / price alignment interest | price alignment interest (PAI)
02 | collateral choice option | option de choix du collatéral
02 | discounting switch | changement d'actualisation
03 | bucketed sensitivity / bucketed sensitivities | sensibilité par pilier / sensibilités par pilier
03 | risk ladder | échéancier de risque (risk ladder)
03 | curve Jacobian | jacobienne de la courbe
03 | key-rate duration / key-rate durations | duration partielle / durations partielles (key-rate duration)
03 | level factor | facteur de niveau
03 | slope factor | facteur de pente
03 | curvature factor | facteur de courbure
03 | cross-gamma | gamma croisé
04 | lognormal volatility | volatilité lognormale
04 | flat volatility | volatilité plate (flat)
04 | caplet volatility / caplet volatilities | volatilité de caplet / volatilités de caplet
04 | Caplet stripping / caplet stripping | stripping des caplets
04 | cash-settled swaption | swaption à règlement en espèces (cash-settled)
04 | cash annuity | annuité cash
05 | Normal SABR | SABR normal
05 | shifted lognormal model | modèle lognormal décalé (shifted)
05 | Shifted SABR / shifted SABR | SABR décalé (shifted SABR)
05 | effective lower bound | plancher effectif des taux
05 | swaption matrix | matrice des swaptions
05 | volatility cube | cube de volatilité
06 | timing adjustment | ajustement de calendrier (timing adjustment)
06 | constant-maturity swap / constant-maturity swaps | swap CMS / swaps CMS (constant-maturity swap)
06 | CMS convexity adjustment | ajustement de convexité CMS
06 | linear terminal swap-rate model | modèle linéaire du taux swap terminal
06 | CMS spread option / CMS spread options | option sur spread CMS / options sur spread CMS
07 | short-rate model / short-rate models | modèle de taux court / modèles de taux court
07 | affine term-structure model / affine term-structure models | modèle affine de structure par terme / modèles affines de structure par terme
07 | Vasicek model | modèle de Vasicek
07 | Hull--White model | modèle de Hull--White
07 | Black--Karasinski model | modèle de Black--Karasinski
07 | Jamshidian decomposition | décomposition de Jamshidian
07 | two-factor Gaussian model | modèle gaussien à deux facteurs
08 | Heath--Jarrow--Morton framework | cadre de Heath--Jarrow--Morton
08 | HJM drift condition | condition de drift HJM
08 | LIBOR market model | modèle de marché LIBOR (LMM)
08 | spot measure | mesure spot
08 | terminal measure | mesure terminale
08 | swap market model | modèle de marché des swaps
08 | Rebonato's formula | formule de Rebonato
08 | forward-rate correlation | corrélation des taux forward
09 | Bermudan swaption / Bermudan swaptions | swaption bermudéenne / swaptions bermudéennes
09 | co-terminal swaptions | swaptions co-terminales
09 | switch option | option d'échange (switch option)
09 | Formosa bond / Formosa bonds | obligation Formosa / obligations Formosa
09 | callable range accrual | range accrual remboursable par anticipation (callable)
10 | backward-looking rate | taux rétrospectif (backward-looking)
10 | forward-looking term rate | taux à terme prospectif (forward-looking)
10 | backward-looking caplet | caplet rétrospectif
10 | generalised forward market model | modèle de marché forward généralisé (FMM)
10 | Cheyette model | modèle de Cheyette
11 | Jarrow--Yildirim model | modèle de Jarrow--Yildirim
11 | year-on-year inflation swap | swap d'inflation annuel (year-on-year)
11 | year-on-year convexity adjustment | ajustement de convexité year-on-year
11 | inflation cap | cap d'inflation
11 | Limited price indexation / limited price indexation | indexation plafonnée (limited price indexation, LPI)
12 | prepayment model | modèle de remboursement anticipé
12 | Housing turnover / housing turnover | rotation du parc immobilier (housing turnover)
12 | refinancing incentive | incitation au refinancement
12 | prepayment S-curve | courbe en S du remboursement anticipé
12 | Burnout / burnout | essoufflement (burnout)
12 | current coupon | coupon courant
12 | primary--secondary spread | spread primaire--secondaire
12 | option cost | coût de l'option
12 | interest-only strip | strip intérêts seuls (interest-only, IO)
12 | principal-only strip | strip principal seul (principal-only, PO)
13 | reduced-form model / reduced-form models | modèle à forme réduite / modèles à forme réduite
13 | probability of default | probabilité de défaut
13 | loss given default | perte en cas de défaut (LGD)
13 | risky discount factor | facteur d'actualisation risqué
13 | risky annuity | annuité risquée
13 | credit triangle | triangle du crédit
13 | ISDA standard model | modèle standard de l'ISDA
13 | CS01 | CS01 [masculine: le CS01]
13 | Jump-to-default risk / jump-to-default risk | risque de saut au défaut (jump-to-default)
13 | default risk premium | prime de risque de défaut
14 | structural model / structural models | modèle structurel / modèles structurels
14 | Merton model | modèle de Merton
14 | distance to default | distance au défaut
14 | first-passage model | modèle de premier passage
14 | default barrier | barrière de défaut
14 | Capital-structure arbitrage / capital-structure arbitrage | arbitrage de structure du capital
15 | default correlation | corrélation de défaut
15 | Gaussian copula | copule gaussienne
15 | large homogeneous pool | grand portefeuille homogène (large homogeneous pool, LHP)
15 | compound correlation | corrélation composée (compound)
15 | tranche delta | delta de tranche
15 | super senior tranche | tranche super senior
15 | Student-t copula | copule de Student
16 | Schwartz--Smith model | modèle de Schwartz--Smith
16 | spread option / spread options | option sur spread / options sur spread
16 | Kirk's approximation | approximation de Kirk
16 | intrinsic storage value | valeur intrinsèque du stockage
16 | extrinsic value | valeur extrinsèque
16 | rolling intrinsic | intrinsèque glissant (rolling intrinsic)
17 | Counterparty credit risk / counterparty credit risk | risque de crédit de contrepartie
17 | counterparty exposure | exposition de contrepartie
17 | expected exposure | exposition attendue (EE)
17 | expected negative exposure | exposition négative attendue (ENE)
17 | potential future exposure | exposition future potentielle (PFE)
17 | expected positive exposure | exposition positive attendue (EPE)
17 | netting set / netting sets | ensemble de compensation / ensembles de compensation (netting set)
17 | Close-out netting / close-out netting | compensation avec déchéance du terme (close-out netting)
17 | collateral threshold | seuil de collatéralisation
17 | minimum transfer amount | montant minimal de transfert
17 | independent amount | montant indépendant (independent amount)
17 | Wrong-way risk / wrong-way risk | risque de corrélation défavorable (wrong-way risk)
18 | credit valuation adjustment | ajustement de valeur pour risque de crédit (CVA)
18 | debit valuation adjustment | ajustement de valeur pour risque de crédit propre (DVA)
18 | bilateral CVA | CVA bilatérale [la CVA, feminine]
18 | close-out amount | montant de résiliation (close-out amount)
18 | XVA | XVA [les XVA]
19 | funding valuation adjustment | ajustement de valeur pour financement (FVA)
19 | funding cost adjustment | ajustement pour coût de financement (FCA)
19 | funding benefit adjustment | ajustement pour bénéfice de financement (FBA)
19 | margin valuation adjustment | ajustement de valeur pour marge (MVA)
19 | exposure at default | exposition en cas de défaut (EAD)
19 | standardised approach for counterparty credit risk | approche standard pour le risque de crédit de contrepartie (SA-CCR)
19 | CVA risk capital | exigence de fonds propres au titre du risque de CVA
19 | capital valuation adjustment | ajustement de valeur pour fonds propres (KVA)
19 | hurdle rate | taux de rendement minimal exigé (hurdle rate)
20 | XVA desk | desk XVA
20 | incremental XVA | XVA incrémentale
20 | Euler allocation | allocation d'Euler
20 | proxy credit spread / proxy credit spreads | spread de crédit de substitution / spreads de crédit de substitution (proxy)
20 | contingent credit default swap | CDS contingent (contingent credit default swap)
20 | XVA charge | charge XVA
21 | risk factor / risk factors | facteur de risque / facteurs de risque
21 | value at risk | valeur en risque (VaR)
21 | Historical simulation / historical simulation | simulation historique
21 | Parametric value at risk / parametric value at risk | VaR paramétrique
21 | Monte Carlo value at risk | VaR Monte Carlo
21 | Filtered historical simulation / filtered historical simulation | simulation historique filtrée
21 | delta--gamma approximation | approximation delta--gamma
21 | square-root-of-time rule | règle de la racine carrée du temps
21 | expected shortfall | expected shortfall (ES) [l'expected shortfall, masculine]
21 | coherent risk measure / coherent risk measures | mesure de risque cohérente / mesures de risque cohérentes
21 | VaR exception / VaR exceptions | dépassement de VaR / dépassements de VaR
21 | Kupiec test | test de Kupiec
21 | Christoffersen test | test de Christoffersen
21 | traffic-light test | test des feux tricolores
22 | stress test / stress tests | test de résistance / tests de résistance (stress test)
22 | historical scenario / historical scenarios | scénario historique / scénarios historiques
22 | hypothetical scenario / hypothetical scenarios | scénario hypothétique / scénarios hypothétiques
22 | Scenario conditioning / scenario conditioning | conditionnement de scénario
22 | reverse stress test | test de résistance inversé (reverse stress test)
22 | supervisory stress test / supervisory stress tests | test de résistance prudentiel / tests de résistance prudentiels
23 | Fundamental Review of the Trading Book | Fundamental Review of the Trading Book (FRTB) [la FRTB]
23 | trading book | portefeuille de négociation (trading book)
23 | banking book | portefeuille bancaire (banking book)
23 | sensitivities-based method | méthode fondée sur les sensibilités
23 | curvature risk charge | exigence au titre du risque de courbure
23 | default risk charge | exigence au titre du risque de défaut
23 | residual risk add-on | majoration pour risque résiduel
23 | internal models approach | approche des modèles internes (IMA)
23 | liquidity horizons / liquidity horizon | horizons de liquidité / horizon de liquidité
23 | Stressed expected shortfall / stressed expected shortfall | expected shortfall en période de tensions
23 | hypothetical P\&L | P\&L hypothétique
23 | risk-theoretical P\&L | P\&L théorique du risque
23 | P\&L attribution test | test d'attribution du P\&L
23 | risk-factor eligibility test | test d'éligibilité des facteurs de risque
23 | non-modellable risk factor / non-modellable risk factors | facteur de risque non modélisable / facteurs de risque non modélisables
24 | liquidity coverage ratio | ratio de liquidité à court terme (LCR)
24 | high-quality liquid assets | actifs liquides de haute qualité (HQLA)
24 | net stable funding ratio | ratio de financement stable net (NSFR)
24 | Funds-transfer pricing / funds-transfer pricing | taux de cession interne (funds-transfer pricing, FTP)
24 | Asset--liability management / asset--liability management | gestion actif--passif (ALM)
24 | interest-rate risk in the banking book | risque de taux du portefeuille bancaire (IRRBB)
24 | economic value of equity | valeur économique des fonds propres (EVE)
24 | Net interest income sensitivity / net interest income sensitivity | sensibilité de la marge nette d'intérêt (NII)
24 | non-maturity deposit / non-maturity deposits | dépôt sans échéance / dépôts sans échéance
24 | deposit beta | bêta des dépôts
24 | held-to-maturity portfolio | portefeuille détenu jusqu'à l'échéance
24 | bank run | panique bancaire (bank run)
25 | initial-margin model / initial-margin models | modèle de marge initiale / modèles de marge initiale
25 | standard initial margin model | modèle standard de marge initiale (SIMM)
25 | Schedule-based initial margin / schedule-based initial margin | marge initiale par barème
25 | initial-margin threshold | seuil de marge initiale
25 | anti-procyclicality tool / anti-procyclicality tools | outil anti-procyclicité / outils anti-procyclicité
25 | concentration add-on | majoration pour concentration
26 | Model risk / model risk | risque de modèle
26 | Model risk management / model risk management | gestion du risque de modèle
26 | Effective challenge / effective challenge | remise en cause effective (effective challenge)
26 | three lines of defence | trois lignes de défense
26 | Model validation / model validation | validation des modèles
26 | benchmark model / benchmark models | modèle de référence / modèles de référence (benchmark)
26 | Outcomes analysis / outcomes analysis | analyse des résultats
26 | model inventory | inventaire des modèles
26 | Model tiering / model tiering | hiérarchisation des modèles (tiering)
26 | post-model adjustment / post-model adjustments | ajustement post-modèle / ajustements post-modèle
27 | Risk-based attribution / risk-based attribution | explication par les sensibilités (risk-based)
27 | Revaluation-based attribution / revaluation-based attribution | explication par réévaluation
27 | unexplained P\&L | P\&L inexpliqué
27 | Product control / product control | product control [le product control]
27 | Independent price verification / independent price verification | vérification indépendante des prix (IPV)
27 | fair-value hierarchy | hiérarchie de la juste valeur
27 | Prudent valuation / prudent valuation | évaluation prudente
27 | additional valuation adjustments | corrections de valeur supplémentaires (AVA)
28 | Operational risk / operational risk | risque opérationnel
28 | operational loss event / operational loss events | événement de perte opérationnelle / événements de perte opérationnelle
28 | Rogue trading / rogue trading | fraude de trader (rogue trading)
28 | fictitious trade / fictitious trades | opération fictive / opérations fictives
28 | Segregation of duties / segregation of duties | séparation des tâches
28 | Block leave / block leave | congés obligatoires consécutifs (block leave)
29 | risk engine | moteur de risque
29 | Risk data aggregation / risk data aggregation | agrégation des données de risque
29 | Full revaluation / full revaluation | réévaluation complète
29 | revaluation grid | grille de réévaluation
29 | risk hierarchy | hiérarchie de risque
29 | risk limit / risk limits | limite de risque / limites de risque
