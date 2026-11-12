# Glossary — One Quant Book 15 (`platforms`) in French

Written by the coordinator (claude-opus-5-5) on 2026-11-12; same rules as `GLOSSARY_BOOK_1_FR.md`. This file lists
Book 15's own defined terms; the run uses `GLOSSARY_BOOK_15_FR.run.md`, which adds every earlier book's lines as `00`.
Platform engineers keep tool names and some design words in English (tick store, dataframe, monorepo, event sourcing, runbook); the data and back-office notions take the French of French banks (rapprochement, saisie des transactions, instruction de règlement).

01 | front-to-back flow | flux front-to-back
01 | data-flow map | carte des flux de données
01 | system of record | système de référence (system of record)
01 | golden source | source de référence (golden source)
01 | Batch processing / batch processing | traitement par lots (batch)
01 | Stream processing / stream processing | traitement en flux (streaming)
01 | end-of-day batch | batch de fin de journée
01 | blast radius | rayon d'impact (blast radius)
02 | Tick data / tick data | données tick
02 | raw capture | capture brute
02 | compression ratio | taux de compression
02 | Partitioning / partitioning | partitionnement
02 | partition key | clé de partition
02 | storage tier | niveau de stockage
02 | retention policy | politique de rétention
03 | row-oriented layout | disposition orientée lignes
03 | columnar layout | disposition en colonnes
03 | validity bitmap | bitmap de validité
03 | row group | groupe de lignes (row group)
03 | column chunk | bloc de colonne (column chunk)
03 | data pages | pages de données / page de données
03 | Dictionary encoding / dictionary encoding | encodage par dictionnaire
03 | Run-length encoding / run-length encoding | codage par plages (run-length encoding)
03 | Delta encoding / delta encoding | encodage delta
03 | Bit packing / bit packing | compactage de bits (bit packing)
03 | zone map | carte de zones (zone map)
03 | Predicate pushdown / predicate pushdown | report des prédicats (predicate pushdown)
03 | Projection pushdown / projection pushdown | report des projections (projection pushdown)
04 | tick store | base de ticks (tick store)
04 | append-only file | fichier en ajout seul (append-only)
04 | flat file format | format de fichier plat
04 | schema version | version de schéma
04 | End-of-day compaction / end-of-day compaction | compactage de fin de journée
04 | sort key | clé de tri
04 | intraday store | base intrajournalière
04 | historical store | base historique
04 | memory-mapped file | fichier projeté en mémoire (memory-mapped)
04 | Schema evolution / schema evolution | évolution de schéma
05 | time-series database | base de données de séries temporelles
05 | time bucket | intervalle de temps (bucket)
05 | Downsampling / downsampling | sous-échantillonnage
05 | embedded database | base de données embarquée
05 | Vectorised query execution / vectorised query execution | exécution vectorisée des requêtes
05 | Late materialisation / late materialisation | matérialisation tardive
06 | reference-data service | service de données de référence
06 | golden copy | copie de référence (golden copy)
06 | Symbol resolution / symbol resolution | résolution des symboles
06 | corporate-action event | événement d'opération sur titres
06 | instrument lifecycle event | événement de cycle de vie de l'instrument
06 | counterparty master | référentiel des contreparties
07 | data-quality rule | règle de qualité des données
07 | data contract | contrat de données
07 | anomaly flag | indicateur d'anomalie
07 | quarantine | quarantaine
07 | cross-source check | contrôle inter-sources
07 | vendor correction | correction du fournisseur
07 | data lineage | lignage des données
07 | provenance record | fiche de provenance
08 | interpreter overhead | surcoût de l'interpréteur
08 | Array programming / array programming | programmation par tableaux
08 | Chunked processing / chunked processing | traitement par blocs
08 | peak resident memory | pic de mémoire résidente
08 | global interpreter lock | verrou global de l'interpréteur (GIL)
08 | Process-based parallelism / process-based parallelism | parallélisme par processus
08 | serialisation cost | coût de sérialisation
09 | native extension | extension native / extensions natives
09 | language binding | liaison de langage (binding)
09 | foreign function interface | interface de fonctions étrangères (FFI)
09 | application binary interface | interface binaire d'application (ABI)
09 | boundary-crossing cost | coût de franchissement de la frontière
09 | buffer protocol | protocole de tampon (buffer protocol)
10 | dataframe | dataframe / dataframes
10 | long format | format long
10 | wide format | format large
10 | eager evaluation | évaluation immédiate (eager)
10 | lazy evaluation | évaluation paresseuse (lazy)
10 | query optimiser | optimiseur de requêtes
10 | Out-of-core processing / out-of-core processing | traitement hors mémoire (out-of-core)
10 | Streaming execution / streaming execution | exécution en flux
10 | window function | fonction de fenêtre
11 | backtest engine | moteur de backtest
11 | event model | modèle d'événements
11 | data-access layer | couche d'accès aux données
11 | results store | base de résultats
11 | reactive simulation | simulation réactive
12 | Simulation--production parity | parité simulation--production
12 | strategy host | hôte de stratégie
12 | environment adapter | adaptateur d'environnement
12 | market-data abstraction | abstraction des données de marché
12 | order-entry abstraction | abstraction de la saisie d'ordres
12 | parity harness | harnais de parité
13 | compute cluster | grappe de calcul (cluster)
13 | job scheduler | ordonnanceur de tâches
13 | embarrassingly parallel | trivialement parallèle (embarrassingly parallel)
13 | parameter sweep | balayage de paramètres
13 | makespan | durée totale (makespan)
13 | straggler | traînard (straggler)
13 | Fair-share scheduling / fair-share scheduling | ordonnancement à parts équitables (fair share)
13 | Work stealing / work stealing | vol de tâches (work stealing)
13 | task graph | graphe de tâches
13 | Speculative execution / speculative execution | exécution spéculative
14 | host--device transfer | transfert hôte--périphérique
14 | Thread divergence / thread divergence | divergence des threads
14 | arithmetic intensity | intensité arithmétique
14 | roofline model | modèle roofline
14 | memory-bound | limité par la mémoire (memory-bound)
14 | compute-bound | limité par le calcul (compute-bound)
15 | computational notebook | notebook de calcul
15 | hidden state | état caché
15 | research library | bibliothèque de recherche
15 | Code review / code review | revue de code
15 | monorepo | monorepo
15 | container image | image de conteneur
16 | signal service | service de signaux
16 | parameter store | magasin de paramètres
16 | Configuration as data / configuration as data | configuration comme donnée
16 | configuration schema | schéma de configuration
16 | feature flag | indicateur de fonctionnalité (feature flag)
16 | Configuration drift / configuration drift | dérive de configuration
17 | position service | service de positions
17 | execution identifier | identifiant d'exécution
17 | trade bust | annulation de transaction (trade bust)
17 | Intraday P\&L / intraday P\&L | P\&L intrajournalier
17 | end-of-day mark | valorisation de fin de journée
17 | start-of-day position | position de début de journée
17 | trade-date position | position en date de négociation
17 | settlement-date position | position en date de règlement
18 | real-time risk system | système de risque en temps réel
18 | Exposure aggregation / exposure aggregation | agrégation des expositions
18 | Incremental aggregation / incremental aggregation | agrégation incrémentale
18 | sensitivity cache | cache de sensibilités
18 | risk snapshot | instantané de risque
18 | what-if check | contrôle what-if
19 | analytics library | bibliothèque analytique
19 | market object | objet de marché
19 | payoff scripting language | langage de script de payoff
19 | payoff script | script de payoff
19 | observer pattern | motif observateur
19 | Lazy recalculation / lazy recalculation | recalcul paresseux
20 | risk grid | grille de risque
20 | batch window | fenêtre de batch
20 | Scenario fan-out / scenario fan-out | distribution des scénarios (fan-out)
20 | Task granularity / task granularity | granularité des tâches
20 | Incremental revaluation / incremental revaluation | réévaluation incrémentale
21 | canonical trade model | modèle canonique de transaction
21 | unique transaction identifier | identifiant unique de transaction (UTI)
21 | Trade capture / trade capture | saisie des transactions (trade capture)
21 | Booking / booking | enregistrement (booking)
21 | booking model | modèle d'enregistrement (booking model)
21 | trade lifecycle event | événement de cycle de vie de la transaction
21 | trade amendment | modification de transaction
21 | block allocation | allocation de bloc
21 | Straight-through processing / straight-through processing | traitement de bout en bout (straight-through processing)
22 | trade confirmation | confirmation de transaction
22 | Affirmation / affirmation | affirmation
22 | settlement instruction | instruction de règlement
22 | standard settlement instruction | instruction de règlement permanente (SSI)
22 | Confirmation matching / confirmation matching | rapprochement des confirmations
22 | matching tolerance | tolérance de rapprochement
22 | Reconciliation / reconciliation | rapprochement (reconciliation)
22 | reconciliation break | écart de rapprochement (break)
22 | Break ageing / break ageing | vieillissement des écarts
23 | market-data distribution platform | plateforme de distribution des données de marché
23 | unit of count | unité de comptage
23 | entitlement | droit d'accès (entitlement) / droits d'accès
23 | entitlement system | système de droits d'accès
23 | usage report | rapport d'utilisation
23 | market-data audit | audit des données de marché
23 | Derived data / derived data | données dérivées
24 | Publish--subscribe | publication--abonnement (publish--subscribe)
24 | message broker | courtier de messages (message broker)
24 | brokerless messaging | messagerie sans courtier
24 | partitioned log | journal partitionné
24 | consumer offset | position du consommateur (offset)
24 | consumer group | groupe de consommateurs
24 | at-most-once delivery | livraison au plus une fois
24 | at-least-once delivery | livraison au moins une fois
24 | Exactly-once processing / exactly-once processing | traitement exactement une fois
24 | transactional outbox | boîte d'envoi transactionnelle (outbox)
24 | Event sourcing / event sourcing | event sourcing
24 | dead-letter queue | file des messages en échec (dead-letter queue)
25 | relational model | modèle relationnel
25 | primary key | clé primaire
25 | foreign key | clé étrangère
25 | normal form | forme normale
25 | ACID transaction | transaction ACID
25 | isolation level | niveau d'isolation
25 | write-ahead log | journal d'écriture anticipée (write-ahead log)
25 | B-tree index | index en arbre B
25 | query plan | plan de requête
25 | system time | temps système
25 | time-travel query | requête temporelle (time travel)
25 | Online transaction processing / online transaction processing | traitement transactionnel en ligne (OLTP)
25 | Online analytical processing / online analytical processing | traitement analytique en ligne (OLAP)
26 | Infrastructure as code / infrastructure as code | infrastructure as code
26 | On-demand capacity / on-demand capacity | capacité à la demande
26 | Reserved capacity / reserved capacity | capacité réservée
26 | Spot capacity / spot capacity | capacité spot
26 | Cloud bursting / cloud bursting | débordement vers le cloud (cloud bursting)
26 | Data gravity / data gravity | gravité des données
26 | shared responsibility model | modèle de responsabilité partagée
27 | unit test | test unitaire / tests unitaires
27 | integration test | test d'intégration
27 | end-to-end test | test de bout en bout
27 | test pyramid | pyramide des tests
27 | golden-file test | test sur fichier de référence (golden file)
27 | Continuous integration / continuous integration | intégration continue
27 | deployment pipeline | chaîne de déploiement (pipeline)
27 | Continuous delivery / continuous delivery | livraison continue
27 | release train | train de livraisons (release train)
27 | Change control / change control | contrôle des changements
27 | blue--green deployment | déploiement bleu--vert
27 | rollback | retour arrière (rollback)
28 | Observability / observability | observabilité
28 | metric | métrique / métriques
28 | Structured logging / structured logging | journalisation structurée
28 | Distributed tracing / distributed tracing | traçage distribué
28 | span | span
28 | service-level indicator | indicateur de niveau de service (SLI)
28 | service-level objective | objectif de niveau de service (SLO)
28 | error budget | budget d'erreur
28 | burn-rate alert | alerte de vitesse de consommation (burn rate)
28 | time to detect | délai de détection
28 | time to restore | délai de rétablissement
28 | on-call rotation | rotation d'astreinte
28 | runbook | procédure d'exploitation (runbook)
28 | incident commander | responsable d'incident (incident commander)
28 | blameless review | revue sans recherche de coupable (blameless)
29 | threat model | modèle de menace
29 | Least privilege / least privilege | moindre privilège
29 | Role-based access control / role-based access control | contrôle d'accès par rôle (RBAC)
29 | Multi-factor authentication / multi-factor authentication | authentification multifacteur
29 | Secrets management / secrets management | gestion des secrets
29 | Secret rotation / secret rotation | rotation des secrets
29 | hardware security module | module matériel de sécurité (HSM)
29 | withdrawal allow-list | liste blanche de retraits
29 | Network segmentation / network segmentation | segmentation du réseau
29 | zero-trust architecture | architecture zero trust
29 | insider threat | menace interne
29 | Data-loss prevention / data-loss prevention | prévention des fuites de données (DLP)
30 | trade surveillance system | système de surveillance des transactions
30 | surveillance alert | alerte de surveillance
30 | Alert triage / alert triage | tri des alertes
30 | case management system | système de gestion des dossiers
30 | communications archive | archive des communications
30 | Communications surveillance / communications surveillance | surveillance des communications
30 | off-channel communication | communication hors canal
30 | Transaction reporting / transaction reporting | déclaration des transactions
