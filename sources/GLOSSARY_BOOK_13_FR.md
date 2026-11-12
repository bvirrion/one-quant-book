# Glossary — One Quant Book 13 (`low-latency`) in French

Written by the coordinator (claude-opus-5-5) on 2026-11-12; same rules as `GLOSSARY_BOOK_1_FR.md`. This file lists
Book 13's own defined terms; the run uses `GLOSSARY_BOOK_13_FR.run.md`, which adds every earlier book's lines as `00`.
French low-latency engineers keep many words in English (hot path, cache, lock-free, feed handler, kernel bypass, drop copy); the glossary gives the French where it is in use and the English in parentheses at the definition.

01 | latency | latence
01 | tick-to-trade latency | latence tick-to-trade
01 | wire-to-wire latency | latence wire-to-wire
01 | hot path | chemin critique (hot path)
01 | tail latency | latence de queue (tail latency)
01 | Jitter / jitter | gigue (jitter)
01 | latency budget | budget de latence
02 | instruction pipeline | pipeline d'instructions
02 | Instructions per cycle / instructions per cycle | instructions par cycle (IPC)
02 | out-of-order execution | exécution dans le désordre (out-of-order)
02 | reorder buffer | tampon de réordonnancement (reorder buffer)
02 | microbenchmark | microbenchmark / microbenchmarks
02 | compiler barrier | barrière de compilation
02 | Branch prediction / branch prediction | prédiction de branchement
02 | branch misprediction | erreur de prédiction de branchement
02 | Dynamic frequency scaling / dynamic frequency scaling | variation dynamique de fréquence
02 | idle state | état de veille (C-state)
02 | time-stamp counter | compteur d'horodatage (TSC)
02 | simultaneous multithreading | multithreading simultané (SMT)
02 | heterogeneous cores | cœurs hétérogènes
03 | cache lines | lignes de cache / ligne de cache
03 | set-associative cache | cache associatif par ensembles
03 | cache miss | défaut de cache (cache miss)
03 | working set | ensemble de travail (working set)
03 | Cache coherence / cache coherence | cohérence de cache
03 | False sharing / false sharing | faux partage (false sharing)
03 | translation lookaside buffer | tampon de traduction d'adresses (TLB)
03 | huge page | grande page (huge page) / grandes pages
03 | Hardware prefetching / hardware prefetching | préchargement matériel
04 | non-uniform memory access | accès mémoire non uniforme (NUMA)
04 | NUMA node | nœud NUMA
04 | first-touch allocation | allocation au premier accès (first touch)
04 | socket interconnect | interconnexion entre sockets
04 | PCI Express | PCI Express
04 | direct memory access | accès direct à la mémoire (DMA)
04 | Direct cache access / direct cache access | accès direct au cache (DCA)
04 | device locality | localité du périphérique
05 | invariant time-stamp counter | compteur d'horodatage invariant
05 | measurement overhead | surcoût de mesure
05 | hardware timestamp | horodatage matériel
05 | latency histogram | histogramme de latence
05 | Coordinated omission / coordinated omission | omission coordonnée (coordinated omission)
05 | sampling profiler | profileur par échantillonnage
05 | hardware performance counter | compteur de performance matériel
06 | structure padding | remplissage de structure (padding)
06 | page fault | défaut de page
06 | Pre-faulting / pre-faulting | pré-chargement des pages (pre-faulting)
06 | arena allocator | allocateur par arène
06 | object pool | réserve d'objets (object pool)
06 | free list | liste libre (free list)
06 | small-buffer optimisation | optimisation des petits tampons (small-buffer optimisation)
06 | fixed-capacity container | conteneur à capacité fixe
07 | dynamic dispatch | répartition dynamique (dynamic dispatch)
07 | Devirtualisation / devirtualisation | dévirtualisation
07 | Static polymorphism / static polymorphism | polymorphisme statique
07 | curiously recurring template pattern | curiously recurring template pattern (CRTP)
07 | Compile-time evaluation / compile-time evaluation | évaluation à la compilation
07 | Inlining / inlining | inlining
07 | cold path | chemin froid (cold path)
08 | Undefined behaviour / undefined behaviour | comportement indéfini
08 | strict aliasing | aliasing strict
08 | Function multiversioning / function multiversioning | multiversionnage de fonctions
08 | profile-guided optimisation | optimisation guidée par profil (PGO)
08 | link-time optimisation | optimisation à l'édition de liens (LTO)
09 | zero-cost abstraction | abstraction à coût nul
09 | Bounds-check elimination / bounds-check elimination | élimination des vérifications de bornes
09 | sound | sain (sound) [Rust; never sûr, which is safe]
09 | global allocator | allocateur global
09 | data race | course aux données (data race)
09 | async runtime | moteur d'exécution asynchrone (async runtime)
10 | garbage collector | ramasse-miettes (garbage collector)
10 | stop-the-world pause | pause stop-the-world
10 | Off-heap memory / off-heap memory | mémoire hors tas (off-heap)
10 | just-in-time compilation | compilation à la volée (JIT)
10 | warm-up period | période de chauffe (warm-up)
10 | Deoptimisation / deoptimisation | désoptimisation
11 | atomic operation | opération atomique
11 | memory ordering | ordonnancement mémoire (memory ordering)
11 | acquire--release ordering | ordonnancement acquire--release
11 | Sequential consistency / sequential consistency | cohérence séquentielle
11 | Compare-and-swap / compare-and-swap | compare-and-swap (CAS)
11 | ABA problem | problème ABA
11 | hazard pointer | pointeur de danger (hazard pointer)
11 | epoch-based reclamation | récupération par époques (epoch-based reclamation)
11 | lock-free | sans verrou (lock-free)
11 | wait-free | sans attente (wait-free)
11 | Priority inversion / priority inversion | inversion de priorité
12 | ring buffer | tampon circulaire (ring buffer)
12 | single-producer single-consumer queue | file à un producteur et un consommateur (SPSC)
12 | disruptor pattern | motif disruptor
12 | sequence lock | verrou à séquence (seqlock)
12 | shared-memory transport | transport par mémoire partagée
12 | Back-pressure / back-pressure | contre-pression (back-pressure)
12 | slow consumer | consommateur lent
12 | Conflation / conflation | conflation
13 | CPU affinity | affinité CPU
13 | Core isolation / core isolation | isolation de cœurs
13 | housekeeping core | cœur de service (housekeeping)
13 | interrupt affinity | affinité des interruptions
13 | tickless kernel | noyau sans tick (tickless)
13 | context switch | changement de contexte
13 | Busy polling / busy polling | attente active (busy polling)
13 | Kernel bypass / kernel bypass | contournement du noyau (kernel bypass)
13 | real-time scheduling policy | politique d'ordonnancement temps réel
13 | Memory locking / memory locking | verrouillage de la mémoire
14 | SIMD | SIMD
14 | vector instruction | instruction vectorielle / instructions vectorielles
14 | Auto-vectorisation / auto-vectorisation | vectorisation automatique
14 | compiler intrinsic | intrinsèque du compilateur / intrinsèques du compilateur
14 | CPU feature dispatch | répartition selon les fonctions du CPU
14 | structure of arrays | structure de tableaux (structure of arrays)
15 | FIX protocol | protocole FIX
15 | tag-value encoding | encodage étiquette-valeur (tag-value)
15 | FIX session | session FIX
15 | heartbeat | heartbeat
15 | resend request | demande de renvoi (resend request)
15 | gap fill | comblement de trou (gap fill)
15 | FIX engine | moteur FIX
16 | flyweight codec | codec flyweight
16 | Multicast / multicast | multicast
16 | message gap | trou de séquence
16 | incremental channel | canal incrémental
16 | snapshot channel | canal d'instantanés (snapshot)
16 | Line arbitration / line arbitration | arbitrage de lignes (line arbitration)
16 | Simple binary encoding / simple binary encoding | Simple Binary Encoding (SBE)
17 | REST interface | interface REST
17 | persistent connection | connexion persistante
17 | connection pool | réserve de connexions (connection pool)
17 | TLS handshake | poignée de main TLS (handshake)
17 | Session resumption / session resumption | reprise de session
17 | WebSocket / webSocket | WebSocket
17 | WebSocket frame / webSocket frame | trame WebSocket
18 | feed handler | feed handler
18 | stale-book flag | indicateur de carnet périmé
18 | recovery latency | latence de reprise
18 | message burst | rafale de messages
18 | receive buffer overrun | débordement du tampon de réception
19 | book builder | constructeur de carnet (book builder)
19 | Open addressing / open addressing | adressage ouvert
20 | event loop | boucle d'événements
20 | Run-to-completion processing / run-to-completion processing | traitement jusqu'à complétion (run-to-completion)
20 | timer wheel | roue de temporisateurs (timer wheel)
20 | injected clock | horloge injectée
21 | order gateway | passerelle d'ordres
21 | order state machine | automate d'état de l'ordre
21 | in-flight order | ordre en vol (in-flight)
21 | cancel--fill race | course annulation--exécution
21 | token bucket | seau à jetons (token bucket)
21 | drop copy | drop copy
22 | risk gate | barrière de risque (risk gate)
22 | fail-closed design | conception à défaillance fermée (fail-closed)
22 | worst-case exposure | exposition dans le pire cas
22 | mass cancel | annulation de masse (mass cancel)
23 | binary log | journal binaire
23 | Deferred formatting / deferred formatting | formatage différé
23 | input journal | journal des entrées
23 | deterministic replay | rejeu déterministe
24 | sequencer architecture | architecture à séquenceur
24 | replicated state machine | machine à états répliquée
24 | Primary--backup replication | réplication primaire--secours
24 | failover | bascule (failover)
24 | Split brain / split brain | split brain
24 | idempotently | de façon idempotente
25 | property-based test | test par propriétés (property-based)
25 | differential test | test différentiel
25 | Fuzz testing / fuzz testing | test par fuzzing
25 | Exchange certification / exchange certification | certification par la bourse
25 | performance regression gate | barrière de régression de performance
26 | instrumentation point | point d'instrumentation
26 | Latency attribution / latency attribution | attribution de la latence
