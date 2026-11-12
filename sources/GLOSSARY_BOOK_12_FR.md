# Glossary — One Quant Book 12 (`ml`) in French

Written by the coordinator (claude-opus-5-5) on 2026-11-12; same rules as `GLOSSARY_BOOK_1_FR.md`. This file lists
Book 12's own defined terms; the run uses `GLOSSARY_BOOK_12_FR.run.md`, which adds every earlier book's lines as `00`.
French ML practice uses the French of the textbooks for the notions (apprentissage supervisé, surapprentissage, réseau de neurones, plongement) and keeps product and method names in English (gradient boosting, transformer, dropout, feature store); feature is variable, as in Book 7.

01 | Supervised learning / supervised learning | apprentissage supervisé
01 | Unsupervised learning / unsupervised learning | apprentissage non supervisé
01 | training set | ensemble d'entraînement
01 | hyperparameter | hyperparamètre / hyperparamètres
01 | validation set | ensemble de validation
01 | test set | ensemble de test
01 | generalisation error | erreur de généralisation
01 | Overfitting / overfitting | surapprentissage (overfitting)
01 | bias--variance decomposition | décomposition biais--variance
01 | out-of-sample R-squared | R² hors échantillon
01 | predictability ceiling | plafond de prévisibilité
02 | fixed-horizon label | étiquette à horizon fixe
02 | triple-barrier label | étiquette à triple barrière
02 | Meta-labelling / meta-labelling | méta-étiquetage (meta-labelling)
02 | label concurrency | concurrence des étiquettes
02 | average uniqueness | unicité moyenne
02 | sample weight | poids d'échantillon
02 | time-decay weight | poids à décroissance temporelle
02 | sequential bootstrap | bootstrap séquentiel
03 | Model selection / model selection | sélection de modèle
03 | hyperparameter search | recherche d'hyperparamètres
03 | Nested cross-validation / nested cross-validation | validation croisée imbriquée
03 | Target leakage / target leakage | fuite de la cible (target leakage)
03 | Train--test contamination | contamination entraînement--test
03 | Adversarial validation / adversarial validation | validation adverse (adversarial validation)
03 | leakage audit | audit de fuite
04 | baseline model | modèle de référence (baseline)
04 | regularisation path | chemin de régularisation
04 | Principal component regression / principal component regression | régression sur composantes principales
04 | Partial least squares / partial least squares | moindres carrés partiels (PLS)
04 | Logistic regression / logistic regression | régression logistique
04 | basis expansion | expansion sur une base de fonctions
05 | decision tree | arbre de décision / arbres de décision
05 | Bagging / bagging | bagging
05 | random forest | forêt aléatoire / forêts aléatoires
05 | out-of-bag error | erreur hors sac (out-of-bag)
05 | Gradient boosting / gradient boosting | gradient boosting
05 | learning rate | taux d'apprentissage
05 | Early stopping / early stopping | arrêt précoce (early stopping)
05 | monotonic constraint | contrainte de monotonie
06 | Feature engineering / feature engineering | construction de variables (feature engineering)
06 | Feature selection / feature selection | sélection de variables
06 | Stability selection / stability selection | sélection par stabilité
06 | mean decrease in impurity | diminution moyenne d'impureté (MDI)
06 | permutation importance | importance par permutation
06 | Shapley value / shapley value | valeur de Shapley
06 | SHAP value | valeur SHAP
06 | substitution effect | effet de substitution
06 | Clustered feature importance / clustered feature importance | importance des variables par grappes (clustered feature importance)
07 | neural network | réseau de neurones / réseaux de neurones
07 | multilayer perceptron | perceptron multicouche
07 | activation function | fonction d'activation
07 | Backpropagation / backpropagation | rétropropagation
07 | mini-batch | mini-lot (mini-batch)
07 | epoch | époque
07 | Adam / adam | Adam
07 | Weight decay / weight decay | décroissance des poids (weight decay)
07 | Dropout / dropout | dropout
07 | Batch normalisation / batch normalisation | normalisation par lot (batch normalisation)
07 | layer normalisation | normalisation par couche (layer normalisation)
07 | deep ensemble | ensemble profond (deep ensemble)
08 | convolutional neural network | réseau de neurones convolutif
08 | recurrent neural network | réseau de neurones récurrent
08 | long short-term memory | mémoire à long et court terme (LSTM)
08 | causal convolution | convolution causale
08 | temporal convolutional network | réseau convolutif temporel (TCN)
08 | attention mechanism | mécanisme d'attention
08 | transformer | transformer
09 | pooled panel model | modèle de panel poolé
09 | permutation-invariant network | réseau invariant par permutation
09 | entity embedding | plongement d'entité (entity embedding)
09 | Instrumented principal component analysis / instrumented principal component analysis | analyse en composantes principales instrumentée (IPCA)
09 | autoencoder | autoencodeur / autoencodeurs
09 | conditional autoencoder | autoencodeur conditionnel
10 | Representation learning / representation learning | apprentissage de représentations
10 | denoising autoencoder | autoencodeur débruiteur
10 | Self-supervised learning / self-supervised learning | apprentissage auto-supervisé
10 | Pre-training / pre-training | pré-entraînement
10 | fine-tuning | ajustement fin (fine-tuning)
10 | linear probe | sonde linéaire (linear probe)
10 | Data augmentation / data augmentation | augmentation de données
10 | Contrastive learning / contrastive learning | apprentissage contrastif
11 | predictive distribution | distribution prédictive
11 | proper scoring rule | règle de score propre (proper scoring rule)
11 | pinball loss | perte pinball
11 | continuous ranked probability score | score de probabilité classé continu (CRPS)
11 | Quantile regression / quantile regression | régression quantile
11 | mixture density network | réseau de densité de mélange
11 | Aleatoric uncertainty / aleatoric uncertainty | incertitude aléatoire
11 | epistemic uncertainty | incertitude épistémique
11 | Conformal prediction / conformal prediction | prédiction conforme
12 | Concept drift / concept drift | dérive conceptuelle (concept drift)
12 | Covariate shift / covariate shift | décalage des covariables (covariate shift)
12 | Online learning / online learning | apprentissage en ligne
12 | Recursive least squares / recursive least squares | moindres carrés récursifs
12 | forgetting factor | facteur d'oubli
12 | drift detector | détecteur de dérive
12 | Page--Hinkley test | test de Page--Hinkley
12 | Adaptive windowing / adaptive windowing | fenêtrage adaptatif (ADWIN)
12 | retraining schedule | calendrier de réentraînement
13 | Tokenisation / tokenisation | tokenisation
13 | bag of words | sac de mots
13 | n-gram | n-gramme / n-grammes
13 | Term frequency--inverse document frequency / term frequency--inverse document frequency | fréquence du terme--fréquence inverse de document (TF-IDF)
13 | topic model | modèle thématique (topic model)
13 | Latent Dirichlet allocation / latent Dirichlet allocation | allocation de Dirichlet latente (LDA)
13 | Event extraction / event extraction | extraction d'événements
13 | word embedding | plongement de mots (word embedding)
13 | Named-entity recognition / named-entity recognition | reconnaissance d'entités nommées
13 | Entity linking / entity linking | liaison d'entités (entity linking)
14 | language model | modèle de langage / modèles de langage
14 | large language model | grand modèle de langage (LLM)
14 | prompt | prompt
14 | context window | fenêtre de contexte
14 | training cut-off | date de coupure de l'entraînement
14 | Retrieval-augmented generation / retrieval-augmented generation | génération augmentée par la recherche (RAG)
14 | BM25 | BM25
14 | hallucination | hallucination
14 | Memorisation / memorisation | mémorisation
14 | anonymisation test | test d'anonymisation
14 | language-model agent | agent à modèle de langage
14 | tool call | appel d'outil
15 | ingestion pipeline | chaîne d'ingestion
15 | Schema validation / schema validation | validation de schéma
15 | Record linkage / record linkage | appariement d'enregistrements (record linkage)
15 | Entity resolution / entity resolution | résolution d'entités
15 | Panel bias / panel bias | biais de panel
15 | Panel reweighting / panel reweighting | repondération du panel
15 | first-seen timestamp | horodatage de première observation
16 | generative model | modèle génératif / modèles génératifs
16 | variational autoencoder | autoencodeur variationnel
16 | generative adversarial network | réseau antagoniste génératif (GAN)
16 | Mode collapse / mode collapse | effondrement de modes (mode collapse)
16 | diffusion model | modèle de diffusion
16 | classifier two-sample test | test à deux échantillons par classifieur
16 | Train-on-synthetic test-on-real / train-on-synthetic test-on-real | entraîner sur le synthétique, tester sur le réel
17 | Reinforcement learning / reinforcement learning | apprentissage par renforcement
17 | Markov decision process / markov decision process | processus de décision markovien
17 | reward | récompense
17 | cumulative reward | récompense cumulée
17 | policy | politique
17 | action-value function | fonction de valeur d'action
17 | Bellman equation / bellman equation | équation de Bellman
17 | Temporal-difference learning / temporal-difference learning | apprentissage par différence temporelle
17 | Q-learning | Q-learning
17 | policy gradient | gradient de politique
17 | actor--critic method | méthode acteur--critique
17 | exploration--exploitation trade-off | arbitrage exploration--exploitation
17 | multi-armed bandit | bandit manchot à plusieurs bras (multi-armed bandit)
17 | contextual bandit | bandit contextuel
17 | Off-policy evaluation / off-policy evaluation | évaluation hors politique (off-policy evaluation)
17 | doubly robust estimator | estimateur doublement robuste
17 | sim-to-real gap | écart simulation--réalité (sim-to-real gap)
18 | Reward shaping / reward shaping | façonnage de la récompense (reward shaping)
18 | Action masking / action masking | masquage d'actions
18 | deep Q-network | réseau Q profond (DQN)
18 | experience replay | rejeu d'expérience (experience replay)
18 | target network | réseau cible
18 | Domain randomisation / domain randomisation | randomisation de domaine
19 | convex risk measure | mesure de risque convexe
19 | entropic risk measure | mesure de risque entropique
19 | indifference price | prix d'indifférence
19 | Deep hedging / deep hedging | couverture profonde (deep hedging)
19 | surrogate model | modèle de substitution (surrogate)
19 | Differential machine learning / differential machine learning | apprentissage automatique différentiel
19 | Deep calibration / deep calibration | calibration profonde
20 | Clustering / clustering | partitionnement (clustering)
20 | k-means | k-moyennes (k-means)
20 | Hierarchical clustering / hierarchical clustering | partitionnement hiérarchique
20 | hidden Markov model | modèle de Markov caché
20 | regime-switching model | modèle à changement de régime
20 | Viterbi algorithm / viterbi algorithm | algorithme de Viterbi
20 | Anomaly detection / anomaly detection | détection d'anomalies
20 | isolation forest | forêt d'isolement (isolation forest)
20 | precision--recall curve | courbe précision--rappel
21 | Interpretability / interpretability | interprétabilité
21 | partial dependence | dépendance partielle
21 | individual conditional expectation | espérance conditionnelle individuelle (ICE)
21 | Accumulated local effects / accumulated local effects | effets locaux accumulés (ALE)
21 | global surrogate | substitut global (global surrogate)
21 | counterfactual explanation | explication contrefactuelle
21 | model card | fiche de modèle (model card)
22 | Predict-then-optimise / predict-then-optimise | prédire puis optimiser
22 | Decision-focused learning / decision-focused learning | apprentissage orienté décision
22 | differentiable optimisation layer | couche d'optimisation différentiable
22 | parametric portfolio policy | politique de portefeuille paramétrique
23 | accelerator | accélérateur / accélérateurs
23 | data loader | chargeur de données (data loader)
23 | memory-mapped dataset | jeu de données projeté en mémoire (memory-mapped)
23 | Mixed-precision training / mixed-precision training | entraînement en précision mixte
23 | bfloat16 | bfloat16
23 | Gradient accumulation / gradient accumulation | accumulation de gradient
23 | Data parallelism / data parallelism | parallélisme de données
23 | model parallelism | parallélisme de modèle
23 | all-reduce | all-reduce
23 | training checkpoint | point de reprise d'entraînement (checkpoint)
24 | feature store | feature store
24 | offline store | magasin hors ligne (offline store)
24 | online store | magasin en ligne (online store)
24 | feature definition | définition de variable
24 | Materialisation / materialisation | matérialisation
24 | Feature freshness / feature freshness | fraîcheur des variables
24 | Training--serving skew | écart entraînement--service (training--serving skew)
25 | experiment tracker | outil de suivi d'expériences (experiment tracker)
25 | run record | fiche d'exécution (run record)
25 | Data versioning / data versioning | versionnage des données
25 | model artefact | artefact de modèle
25 | model registry | registre de modèles
25 | Model lineage / model lineage | lignage du modèle
25 | audit trail | piste d'audit
26 | Inference latency / inference latency | latence d'inférence
26 | Model compilation / model compilation | compilation de modèle
26 | Operator fusion / operator fusion | fusion d'opérateurs
26 | Quantisation / quantisation | quantification
26 | Post-training quantisation / post-training quantisation | quantification post-entraînement
26 | quantisation-aware training | entraînement conscient de la quantification
26 | Dynamic batching / dynamic batching | regroupement dynamique (dynamic batching)
27 | Model monitoring / model monitoring | surveillance des modèles
27 | Prediction drift / prediction drift | dérive des prédictions
27 | population stability index | indice de stabilité de la population (PSI)
27 | performance alarm | alarme de performance
27 | shadow deployment | déploiement fantôme (shadow deployment)
27 | Champion--challenger | champion--challenger
28 | machine-learning engineer | ingénieur en apprentissage automatique (ML engineer)
28 | model owner | propriétaire du modèle
28 | handoff specification | spécification de transmission (handoff)
28 | machine-learning platform | plateforme d'apprentissage automatique
29 | decision staleness | péremption de la décision
