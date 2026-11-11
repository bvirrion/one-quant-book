# Glossary — One Quant Book 10 (`microstructure`) in French

Written by the coordinator (claude-opus-5-5) on 2026-11-11; same rules as `GLOSSARY_BOOK_1_FR.md`. This file lists
Book 10's own defined terms; the run uses `GLOSSARY_BOOK_10_FR.run.md`, which adds every earlier book's lines as `00`.
Execution desks in Paris keep the order types and algorithm names in English (iceberg, peg, VWAP, TWAP, IOC, smart
order router, algo wheel); the market-structure notions take the French of the AMF and ESMA texts (carnet d'ordres,
formation des prix, coupe-circuit).

01 | price level / price levels | niveau de prix / niveaux de prix
01 | order-book event / order-book events | événement du carnet / événements du carnet
01 | matching engine | moteur d'appariement (matching engine)
01 | zero-intelligence model / zero-intelligence models | modèle à intelligence nulle / modèles à intelligence nulle (zero-intelligence)
02 | marketable limit order / marketable limit orders | ordre à cours limité exécutable / ordres à cours limité exécutables
02 | stop-limit order / stop-limit orders | ordre stop à cours limité / ordres stop à cours limité
02 | time in force | durée de validité (time in force)
02 | immediate-or-cancel order / immediate-or-cancel orders | ordre exécuter-ou-annuler / ordres exécuter-ou-annuler (immediate-or-cancel, IOC)
02 | fill-or-kill order / fill-or-kill orders | ordre tout-ou-rien / ordres tout-ou-rien (fill-or-kill, FOK)
02 | good-till-cancelled order / good-till-cancelled orders | ordre à révocation / ordres à révocation (good-till-cancelled, GTC)
02 | hidden order / hidden orders | ordre caché / ordres cachés
02 | iceberg order / iceberg orders | ordre iceberg / ordres iceberg
02 | pegged order / pegged orders | ordre indexé / ordres indexés (pegged order)
02 | midpoint peg | ordre indexé au mid (midpoint peg)
02 | free option of a limit order | option gratuite de l'ordre à cours limité
03 | relative limit price | prix limite relatif
03 | volatility per trade | volatilité par transaction
03 | order lifetime | durée de vie de l'ordre
03 | fleeting order / fleeting orders | ordre fugace / ordres fugaces (fleeting order)
03 | book resilience | résilience du carnet
04 | order-processing cost / order-processing costs | coût de traitement des ordres / coûts de traitement des ordres
04 | inventory-holding cost / inventory-holding costs | coût de détention de l'inventaire / coûts de détention de l'inventaire
04 | informed trader / informed traders | trader informé / traders informés
04 | noise trader / noise traders | noise trader / noise traders [le noise trader]
04 | sequential-trade model / sequential-trade models | modèle à transactions séquentielles / modèles à transactions séquentielles
04 | Glosten--Milgrom model | modèle de Glosten--Milgrom
04 | Kyle model | modèle de Kyle
04 | probability of informed trading | probabilité de transaction informée (PIN)
05 | quoted spread | fourchette affichée (quoted spread)
05 | trade price impact | impact de la transaction sur le prix
05 | adverse-selection component | composante de sélection adverse
05 | spread decomposition | décomposition de la fourchette
05 | Huang--Stoll model | modèle de Huang--Stoll
05 | Madhavan--Richardson--Roomans model | modèle de Madhavan--Richardson--Roomans
05 | low-frequency spread estimator / low-frequency spread estimators | estimateur de fourchette basse fréquence / estimateurs de fourchette basse fréquence
06 | relative tick size | pas de cotation relatif
06 | large-tick asset / large-tick assets | actif à gros tick / actifs à gros tick (large-tick)
06 | small-tick asset / small-tick assets | actif à petit tick / actifs à petit tick (small-tick)
06 | uncertainty-zone model | modèle de zone d'incertitude
06 | queue value | valeur de la position dans la file
06 | difference-in-differences | doubles différences (difference-in-differences)
07 | flat pricing | tarification uniforme (flat pricing)
07 | fee-adjusted price | prix net des frais
07 | effective tick size | pas de cotation effectif
07 | neutral | neutre [a fee schedule with no net rebate]
08 | Market fragmentation / market fragmentation | fragmentation des marchés
08 | protected quote / protected quotes | cotation protégée / cotations protégées
08 | locked | bloqué (locked) [a locked market: bid equals offer across venues]
08 | crossed | croisé (crossed) [a crossed market: bid above offer across venues]
08 | information share | part d'information (information share)
08 | component share | part de composante (component share)
09 | minimum execution quantity | quantité minimale d'exécution
09 | crossing network / crossing networks | réseau de croisement / réseaux de croisement (crossing network)
09 | indication of interest / indications of interest | indication d'intérêt / indications d'intérêt (IOI)
09 | conditional order / conditional orders | ordre conditionnel / ordres conditionnels
09 | firm-up rate | taux de confirmation (firm-up rate)
09 | Information leakage / information leakage | fuite d'information
09 | pinging order / pinging orders | ordre sonde / ordres sondes (pinging)
10 | auction cut-off time | heure limite de l'enchère
10 | auction collar | collar d'enchère
10 | random end | fin aléatoire (random end)
10 | frequent batch auction / frequent batch auctions | enchère par lots fréquente / enchères par lots fréquentes (frequent batch auction)
11 | impact curve / impact curves | courbe d'impact / courbes d'impact
11 | Aggregate impact / aggregate impact | impact agrégé
11 | peak impact | impact maximal
11 | Impact reversion / impact reversion | retour de l'impact (reversion)
11 | impact prefactor | préfacteur d'impact
11 | Alpha contamination / alpha contamination | contamination par l'alpha
12 | propagator model / propagator models | modèle de propagateur / modèles de propagateur
12 | decay kernel | noyau de décroissance
12 | transient impact model / transient impact models | modèle d'impact transitoire / modèles d'impact transitoire
12 | Obizhaeva--Wang model | modèle d'Obizhaeva--Wang
12 | no-dynamic-arbitrage condition | condition d'absence d'arbitrage dynamique
12 | Transaction-triggered price manipulation / transaction-triggered price manipulation | manipulation de prix déclenchée par les transactions
13 | Latent liquidity / latent liquidity | liquidité latente
13 | latent order book | carnet d'ordres latent
13 | locally linear order book | carnet d'ordres localement linéaire
13 | fair pricing condition | condition de prix équitable (fair pricing)
13 | Cross-impact / cross-impact | impact croisé
13 | cross-impact matrix | matrice d'impact croisé
14 | parent order / parent orders | ordre parent / ordres parents
14 | child orders / child order | ordres enfants / ordre enfant
14 | trading trajectory / trading trajectories | trajectoire d'exécution / trajectoires d'exécution
14 | Almgren--Chriss model | modèle d'Almgren--Chriss
14 | Execution risk / execution risk | risque d'exécution
14 | urgency | urgence
14 | efficient trading frontier | frontière d'exécution efficiente
15 | signal-adaptive schedule / signal-adaptive schedules | calendrier adapté au signal / calendriers adaptés au signal
15 | adaptive execution | exécution adaptative
15 | aggressive-in-the-money strategy | stratégie agressive dans la monnaie (aggressive in the money)
15 | bucket-shaped trajectory | trajectoire en baignoire (bucket-shaped)
15 | Stochastic liquidity / stochastic liquidity | liquidité stochastique
16 | execution algorithm / execution algorithms | algorithme d'exécution / algorithmes d'exécution
16 | VWAP algorithm / VWAP algorithms | algorithme VWAP / algorithmes VWAP
16 | TWAP algorithm / TWAP algorithms | algorithme TWAP / algorithmes TWAP
16 | participation algorithm / participation algorithms | algorithme de participation / algorithmes de participation (POV)
16 | implementation-shortfall algorithm / implementation-shortfall algorithms | algorithme d'implementation shortfall / algorithmes d'implementation shortfall
16 | target-close algorithm / target-close algorithms | algorithme de clôture cible / algorithmes de clôture cible (target close)
16 | intraday volume forecast / intraday volume forecasts | prévision de volume intrajournalier / prévisions de volume intrajournalier
16 | dynamic VWAP | VWAP dynamique
17 | order placement problem | problème de placement des ordres
17 | Non-execution risk / non-execution risk | risque de non-exécution
17 | clean-up trade / clean-up trades | transaction de solde / transactions de solde (clean-up)
17 | repricing rule / repricing rules | règle de révision du prix / règles de révision du prix
17 | Queue-aware placement / queue-aware placement | placement tenant compte de la file
18 | smart order router / smart order routers | routeur d'ordres intelligent / routeurs d'ordres intelligents (SOR)
18 | venue ranking | classement des plateformes
18 | spray order / spray orders | ordre dispersé / ordres dispersés (spray)
18 | Quote fade / quote fade | évanouissement de la cotation (quote fade)
18 | Synchronised routing / synchronised routing | routage synchronisé
18 | Anti-gaming logic / anti-gaming logic | logique anti-gaming
19 | execution benchmark / execution benchmarks | référence d'exécution / références d'exécution (benchmark)
19 | pre-trade cost estimate / pre-trade cost estimates | estimation des coûts pré-négociation / estimations des coûts pré-négociation
19 | Slippage attribution / slippage attribution | attribution du slippage
19 | Post-trade reversion / post-trade reversion | retour post-négociation (reversion)
19 | peer-universe comparison | comparaison avec un univers de pairs
20 | order management system / order management systems | système de gestion des ordres (OMS) / systèmes de gestion des ordres
20 | execution management system / execution management systems | système de gestion de l'exécution (EMS) / systèmes de gestion de l'exécution
20 | High-touch trading / high-touch trading | trading high-touch
20 | Low-touch trading / low-touch trading | trading low-touch
20 | algo wheel / algo wheels | algo wheel / algo wheels [la roue d'algorithmes; le terme reste en anglais]
20 | broker scorecard / broker scorecards | grille d'évaluation des courtiers / grilles d'évaluation des courtiers
20 | commission sharing agreement / commission sharing agreements | accord de partage de commissions / accords de partage de commissions (CSA) [not the collateral CSA]
20 | Research unbundling / research unbundling | dissociation de la recherche (unbundling)
21 | liquidity aggregator / liquidity aggregators | agrégateur de liquidité / agrégateurs de liquidité
21 | request for stream | demande de flux de prix (request for stream, RFS)
21 | Firm liquidity / firm liquidity | liquidité ferme
21 | risk transfer price | prix de transfert de risque
22 | agency portfolio trade / agency portfolio trades | transaction de portefeuille en agence / transactions de portefeuille en agence
22 | risk bid / risk bids | risk bid / risk bids [le risk bid]
22 | blind risk bid / blind risk bids | risk bid à l'aveugle / risk bids à l'aveugle
22 | basket liquidity profile | profil de liquidité du panier
23 | over-the-counter search model / over-the-counter search models | modèle de recherche de gré à gré / modèles de recherche de gré à gré
23 | search friction / search frictions | friction de recherche / frictions de recherche
23 | bargaining power | pouvoir de négociation
23 | core--periphery network | réseau cœur--périphérie
23 | Information chasing / information chasing | chasse à l'information
24 | Market quality / market quality | qualité de marché
24 | order-to-trade ratio | ratio ordres sur transactions
24 | Algorithmic trading / algorithmic trading | trading algorithmique
24 | High-frequency trading / high-frequency trading | trading à haute fréquence (HFT)
24 | Hot-potato trading / hot-potato trading | trading de la patate chaude (hot potato)
25 | static price band / static price bands | seuil de réservation statique / seuils de réservation statiques
25 | dynamic price band / dynamic price bands | seuil de réservation dynamique / seuils de réservation dynamiques
25 | trading pause / trading pauses | pause de négociation / pauses de négociation
25 | reopening auction / reopening auctions | enchère de réouverture / enchères de réouverture
25 | Velocity logic / velocity logic | logique de vélocité (velocity logic)
26 | exchange simulator | simulateur de bourse
26 | order-entry protocol / order-entry protocols | protocole de saisie des ordres / protocoles de saisie des ordres
26 | order-entry session / order-entry sessions | session de saisie des ordres / sessions de saisie des ordres
26 | execution report / execution reports | rapport d'exécution / rapports d'exécution
26 | Self-trade prevention / self-trade prevention | prévention de l'auto-appariement (self-trade prevention)
26 | Cancel on disconnect / cancel on disconnect | annulation à la déconnexion (cancel on disconnect)
26 | Redundant feed lines / redundant feed lines | lignes de flux redondantes
26 | Snapshot recovery / snapshot recovery | reprise par instantané (snapshot)
26 | retransmission request / retransmission requests | demande de retransmission / demandes de retransmission
27 | agent-based model / agent-based models | modèle multi-agents / modèles multi-agents
27 | fundamentalist agent / fundamentalist agents | agent fondamentaliste / agents fondamentalistes
27 | chartist agent / chartist agents | agent chartiste / agents chartistes
27 | market-making agent / market-making agents | agent teneur de marché / agents teneurs de marché
27 | method of simulated moments | méthode des moments simulés
28 | participation band | bande de participation
28 | I-would price | prix « I would » [the limit at which the trader would buy more]
