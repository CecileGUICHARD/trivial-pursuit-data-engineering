# Registre des décisions du projet Trivial Pursuit

Ce registre conserve les arbitrages techniques et méthodologiques du projet, de la collecte OpenTDB à la décision de consolider le Silver. Le suivi d’avancement et la description de l’architecture en vigueur restent dans leurs documents respectifs. [Suivi](CURRENT.md) · [Architecture](ARCHITECTURE.md)

Les décisions suivent l’ordre des jalons attestés. Une date de validation figure uniquement lorsqu’une source l’établit. Un commit daté donne un repère documentaire, parfois postérieur au fait. Les notices recensent les solutions envisagées lorsqu’elles sont documentées. Le statut **retenue** décrit un choix validé, dont la mise en œuvre peut rester à faire. **Remplacée** signale un plan ou un jalon ayant un successeur. **Abandonnée** désigne une piste effectivement arrêtée. **Proposée** désigne un point d’arbitrage encore ouvert.

## Sommaire

33 décisions recensées · 27 retenues, 2 abandonnées, 3 remplacées et 1 proposée.

| Décision | Statut |
| --- | --- |
| [DEC-001 · Choisir OpenTDB comme source](#dec-001--choisir-opentdb-comme-source) | retenue |
| [DEC-002 · Adopter l’architecture en médaillon](#dec-002--adopter-larchitecture-en-médaillon) | retenue |
| [DEC-003 · Retenir DuckDB, dbt et Streamlit](#dec-003--retenir-duckdb-dbt-et-streamlit) | retenue |
| [DEC-004 · Conserver le Bronze brut et préparer le Silver en Parquet](#dec-004--conserver-le-bronze-brut-et-préparer-le-silver-en-parquet) | retenue |
| [DEC-005 · Collecter le corpus complet après l’essai de 50 questions](#dec-005--collecter-le-corpus-complet-après-lessai-de-50-questions) | retenue |
| [DEC-006 · Conserver les QCM et les vrai/faux](#dec-006--conserver-les-qcm-et-les-vraifaux) | retenue |
| [DEC-007 · Fixer les axes d’évaluation du benchmark](#dec-007--fixer-les-axes-dévaluation-du-benchmark) | retenue |
| [DEC-008 · Choisir Gemma comme premier LLM local et LM Studio pour l’inférence](#dec-008--choisir-gemma-comme-premier-llm-local-et-lm-studio-pour-linférence) | retenue |
| [DEC-009 · Prévoir une première matrice de prompts P0 à P3](#dec-009--prévoir-une-première-matrice-de-prompts-p0-à-p3) | remplacée |
| [DEC-010 · Organiser le travail autour de scripts et de répertoires dédiés](#dec-010--organiser-le-travail-autour-de-scripts-et-de-répertoires-dédiés) | retenue |
| [DEC-011 · Prévoir un export Silver unique avec une dimension de répétition](#dec-011--prévoir-un-export-silver-unique-avec-une-dimension-de-répétition) | remplacée |
| [DEC-012 · Arbitrer les quatre paires de libellés identiques](#dec-012--arbitrer-les-quatre-paires-de-libellés-identiques) | retenue |
| [DEC-013 · Normaliser les champs texte et typer les distracteurs](#dec-013--normaliser-les-champs-texte-et-typer-les-distracteurs) | retenue |
| [DEC-014 · Tester un premier manifeste sur le jalon dédoublonné](#dec-014--tester-un-premier-manifeste-sur-le-jalon-dédoublonné) | remplacée |
| [DEC-015 · Garder les questions en anglais et limiter les corrections de langue](#dec-015--garder-les-questions-en-anglais-et-limiter-les-corrections-de-langue) | retenue |
| [DEC-016 · Stabiliser les identifiants et figer l’ordre des choix](#dec-016--stabiliser-les-identifiants-et-figer-lordre-des-choix) | retenue |
| [DEC-017 · Versionner les livrables sélectionnés et garder les artefacts de travail locaux](#dec-017--versionner-les-livrables-sélectionnés-et-garder-les-artefacts-de-travail-locaux) | retenue |
| [DEC-018 · Valider un manifeste stratifié et reproductible pour Gemma](#dec-018--valider-un-manifeste-stratifié-et-reproductible-pour-gemma) | retenue |
| [DEC-019 · Écarter cinq variantes encore détectées après normalisation](#dec-019--écarter-cinq-variantes-encore-détectées-après-normalisation) | retenue |
| [DEC-020 · Comparer d’abord les deux prompts P1 et P2](#dec-020--comparer-dabord-les-deux-prompts-p1-et-p2) | retenue |
| [DEC-021 · Rendre les inférences indépendantes au niveau conversationnel](#dec-021--rendre-les-inférences-indépendantes-au-niveau-conversationnel) | retenue |
| [DEC-022 · Appliquer le scoring strict et garder les réponses hors format](#dec-022--appliquer-le-scoring-strict-et-garder-les-réponses-hors-format) | retenue |
| [DEC-023 · Séparer les mesures Bronze et les résultats Silver par modèle et prompt](#dec-023--séparer-les-mesures-bronze-et-les-résultats-silver-par-modèle-et-prompt) | retenue |
| [DEC-024 · Journaliser les tentatives et sauvegarder progressivement](#dec-024--journaliser-les-tentatives-et-sauvegarder-progressivement) | retenue |
| [DEC-025 · Réutiliser les mesures du pilote dans le benchmark complet Gemma](#dec-025--réutiliser-les-mesures-du-pilote-dans-le-benchmark-complet-gemma) | retenue |
| [DEC-026 · Étendre le protocole au prompt P3 d’analyse et de vérification](#dec-026--étendre-le-protocole-au-prompt-p3-danalyse-et-de-vérification) | retenue |
| [DEC-027 · Comparer la faisabilité des candidats sur les mêmes 30 questions](#dec-027--comparer-la-faisabilité-des-candidats-sur-les-mêmes-30-questions) | retenue |
| [DEC-028 · Évaluer Bonsai 27B comme deuxième modèle](#dec-028--évaluer-bonsai-27b-comme-deuxième-modèle) | abandonnée |
| [DEC-029 · Évaluer Qwen3 4B Instruct comme deuxième modèle](#dec-029--évaluer-qwen3-4b-instruct-comme-deuxième-modèle) | abandonnée |
| [DEC-030 · Retenir Ministral comme deuxième modèle complet](#dec-030--retenir-ministral-comme-deuxième-modèle-complet) | retenue |
| [DEC-031 · Archiver les échecs de transport avérés et reprendre les positions non reçues](#dec-031--archiver-les-échecs-de-transport-avérés-et-reprendre-les-positions-non-reçues) | retenue |
| [DEC-032 · Construire une One Big Table dans le Silver consolidé](#dec-032--construire-une-one-big-table-dans-le-silver-consolidé) | retenue |
| [DEC-033 · Préciser le modèle relationnel et le dictionnaire Gold](#dec-033--préciser-le-modèle-relationnel-et-le-dictionnaire-gold) | proposée |

[Informations manquantes et écarts entre les sources](#informations-manquantes-et-écarts-entre-les-sources)

## Initialisation et collecte

### DEC-001 · Choisir OpenTDB comme source

**Statut** retenue.

- **Contexte.** Le cas d’usage pédagogique exige un corpus de questions de culture générale avec des réponses attendues et des caractéristiques exploitables pour l’analyse.
- **Choix et justification.** Utiliser l’API JSON publique d’OpenTDB, accessible sans clé. Elle fournit le type, la difficulté, la catégorie, le libellé, la bonne réponse et les distracteurs.
- **Conséquences et limites.** La collecte dépend du débit et des questions disponibles auprès de l’API. Le projet documente l’attribution à OpenTDB et à ses contributeurs et la redistribution sous CC BY-SA 4.0. Aucun comparatif avec une autre source n’est consigné.
- **Références.** Commit `cdb0286` du 23 novembre 2026. [Source et licence](../README.md#source-des-données)

### DEC-002 · Adopter l’architecture en médaillon

**Statut** retenue.

- **Contexte.** Le projet du cours D42 doit rendre visibles l’extraction, la qualité, les transformations, le stockage et la restitution. Le benchmark fournit le cas d’usage.
- **Choix et justification.** Organiser les données en Bronze pour les sources brutes, Silver pour leur préparation et Gold pour les produits analytiques. Les jalons permettent de rattacher les indicateurs aux données utilisées pour les produire.
- **Conséquences et limites.** Les transformations s’appuient sur des fichiers distincts par étape. La séparation des résultats LLM (DEC-023) et la consolidation Silver (DEC-032) précisent progressivement la même architecture.
- **Références.** Commits `cdb0286` et `cadb884`. [Architecture](ARCHITECTURE.md#choix-validés)

### DEC-003 · Retenir DuckDB, dbt et Streamlit

**Statut** retenue.

- **Contexte.** La chaîne doit transformer des données locales en indicateurs SQL et les restituer dans un tableau de bord.
- **Choix et justification.** Retenir DuckDB pour les lectures Parquet et les traitements SQL locaux, dbt pour organiser les transformations et Streamlit pour la restitution. La première architecture réserve les indicateurs à Gold. La lecture sélective des colonnes Parquet par DuckDB est documentée dès le jalon Bronze.
- **Conséquences et limites.** DuckDB sert déjà aux contrôles et journaux du projet. La répartition future des modèles dbt entre préparation Silver et publication Gold est précisée par DEC-032. Aucun comparatif avec un autre moteur, orchestrateur SQL ou outil de restitution n’est consigné.
- **Références.** Commits `cdb0286` et `cadb884`. [Gold et restitution](ARCHITECTURE.md#gold-et-restitution)

### DEC-004 · Conserver le Bronze brut et préparer le Silver en Parquet

**Statut** retenue.

- **Contexte.** La réponse de l’API est du JSON. Les six champs doivent rester disponibles dans leur état source pour l’audit des transformations.
- **Choix et justification.** Archiver le Bronze OpenTDB en CSV avec `incorrect_answers` sérialisé en JSON dans sa cellule. Laisser le décodage des entités HTML, les corrections et le dédoublonnage au Silver. Convertir d’abord les six champs en Parquet à l’identique, puis conserver les jalons successifs en Parquet pour la lecture typée et sélective.
- **Conséquences et limites.** Le CSV ne porte pas de type liste natif. Le premier Parquet conserve donc le JSON textuel. La conversion en liste intervient avec DEC-013. Les mesures brutes LLM rejoignent le Bronze selon DEC-023.
- **Références.** Commits `cdb0286`, `cadb884` et `4c63216`. [Conversion Parquet](CURRENT.md#conversion-parquet-avant-dédoublonnage) · [Bronze](ARCHITECTURE.md#bronze)

### DEC-005 · Collecter le corpus complet après l’essai de 50 questions

**Statut** retenue · **Collecte** 23 novembre 2026.

- **Contexte et solutions.** Le premier lot vérifie l’appel à l’API et l’export CSV. Sa couverture de 15 catégories ne permet pas de tirer des conclusions sur les modèles. La collecte intégrale des questions accessibles est prévue dès l’initialisation.
- **Choix et justification.** Conserver l’essai comme contrôle technique et constituer le corpus de référence par catégorie, avec des lots d’au plus 50, un délai adapté au débit et un jeton de session pour limiter les répétitions. Le collecteur sauvegarde les compteurs de reprise localement.
- **Conséquences et limites.** Le Bronze complet compte 5 299 questions et 24 catégories. L’expiration du jeton arrête la collecte avec conservation du CSV partiel. L’échantillonnage ultérieur concerne les pilotes LLM (DEC-018).
- **Références.** Commits `cdb0286` et `cadb884`. [Contrôles Bronze](CURRENT.md#contrôles-bronze-du-23-novembre-collecte-complète) · [Collecteur complet](../collect_opentdb_complet.py)

### DEC-006 · Conserver les QCM et les vrai/faux

**Statut** retenue.

- **Contexte.** OpenTDB fournit les types `multiple` et `boolean`, dont les taux de succès au hasard diffèrent.
- **Choix et justification.** Garder les deux types et porter `type` dans le Silver et les analyses. En cas de choix uniforme au hasard, le taux de bonnes réponses vaut 25 % pour un QCM à quatre choix et 50 % pour un vrai/faux.
- **Conséquences et limites.** Le corpus révisé conserve 4 501 QCM et 789 vrai/faux. La composition du corpus doit être connue pour interpréter un score global. Les consignes et valeurs admises varient selon le type (DEC-020 et DEC-022).
- **Références.** Commits `cdb0286` et `cadb884`. [Révision du corpus](CURRENT.md#révision-du-silver-après-les-cinq-arbitrages) · [Protocole](ARCHITECTURE.md#benchmark)

### DEC-007 · Fixer les axes d’évaluation du benchmark

**Statut** retenue.

- **Contexte.** Le projet doit distinguer l’effet du modèle, du prompt et des caractéristiques des questions.
- **Choix et justification.** Comparer l’exactitude, la conformité et les latences moyenne et médiane par modèle. Mesurer l’effet des prompts sur les mêmes questions et ventiler les résultats par catégorie, difficulté et type, avec les effectifs. Les premiers documents prévoient également les croisements catégorie × difficulté et catégorie × prompt.
- **Conséquences et limites.** Les comparaisons appariées rendent lisibles les questions réussies par un seul modèle ou un seul prompt. Le document initial évoque la stabilité et les erreurs communes. Aucun protocole de répétitions dédié à la stabilité n’est attesté pour le lot 4.
- **Références.** Commits `cdb0286` et `cadb884`. [Mesures du benchmark](ARCHITECTURE.md#benchmark) · [Comparaison appariée](CURRENT.md#comparaison-avec-gemma)

### DEC-008 · Choisir Gemma comme premier LLM local et LM Studio pour l’inférence

**Statut** retenue.

- **Contexte.** Le projet compare des LLM exécutés sur la machine du projet. Gemma 4 E2B est identifié en premier dès l’initialisation. La clôture Bronze documente le choix de LM Studio pour servir les modèles localement.
- **Choix et justification.** Utiliser Gemma 4 E2B comme premier modèle de référence et LM Studio comme serveur d’inférence. Le pilote a établi une configuration exploitable avec la quantification Q4_K_M et le moteur Vulkan sur la machine disponible.
- **Conséquences et limites.** Le benchmark de Gemma devient la référence complète du lot 4 (DEC-025 et DEC-026). Le choix du deuxième modèle reste ouvert à ce stade. Le motif initial précis du choix de Gemma, un comparatif avec d’autres serveurs et la date exacte du choix de LM Studio ne sont pas consignés.
- **Références.** Commits `cdb0286`, `cadb884` et `a855785`. [Pilote Gemma](CURRENT.md#pilote-gemma-4-e2b-sur-le-silver-définitif)

### DEC-009 · Prévoir une première matrice de prompts P0 à P3

**Statut** remplacée par DEC-020, puis complétée par DEC-026.

- **Contexte.** Le plan initial veut tester plusieurs formes d’aide apportées par le prompt.
- **Solutions et plan d’origine.** P0 pose directement la question, P1 ajoute un rôle d’expert, P2 autorise la réponse `INCONNU` et P3 indique le domaine.
- **Évolution et justification.** Le protocole ultérieur isole d’abord l’effet du rôle d’expert avec une consigne commune et le même ordre des choix. Il ajoute ensuite des consignes d’analyse et de vérification.
- **Conséquences et limites.** Les noms P1, P2 et P3 ont changé de sens. Les variantes `INCONNU` et indication du domaine restent des pistes du plan initial, sans mesures de benchmark attestées.
- **Références.** Commits `cdb0286` et `cadb884` pour le plan initial, `eca96ea` et `4203835` pour son évolution. [Gabarits exécutés](ARCHITECTURE.md#benchmark)

### DEC-010 · Organiser le travail autour de scripts et de répertoires dédiés

**Statut** retenue.

- **Contexte et solutions.** L’organisation initiale mentionne un répertoire `notebooks/`. Le jalon Bronze formalise une chaîne pilotée par des scripts Python, des modèles SQL dbt et Streamlit.
- **Choix et justification.** Développer sous Debian/WSL avec VS Code et `.venv`, utiliser des chemins portables avec `pathlib` et organiser les données sous `data/`, les modèles sous `dbt/` et l’application sous `app/`. Les consignes du dépôt écartent les notebooks Jupyter pour ce projet.
- **Conséquences et limites.** Les étapes sont documentées par des commandes et des fichiers de référence. Aucun essai comparatif de workflow avec notebooks n’est consigné. Le périmètre Git des données est défini par DEC-017.
- **Références.** Commits `cdb0286` et `cadb884`. [Consignes du dépôt](../AGENTS.md) · [Organisation](../README.md#organisation-du-dépôt)

### DEC-011 · Prévoir un export Silver unique avec une dimension de répétition

**Statut** remplacée par DEC-023. DEC-032 introduit ensuite une consolidation à partir des exports définitifs.

- **Contexte.** Le plan initial envisage plusieurs exécutions pour une question, un modèle et un prompt.
- **Choix envisagé et justification.** Garder les questions préparées à part et rassembler les inférences dans `data/silver/inference_results.parquet`, avec une ligne par question × modèle × prompt × répétition. Le schéma provisoire prévoit `repetition_id`, puis `attempt_id` et `run_id` pour distinguer les tentatives et leur origine.
- **Conséquences et évolution.** Le lot 4 a produit un résultat par question, modèle et prompt, conservé dans des exports séparés avec `inference_id`. L’export unique et les colonnes proposées ci-dessus appartiennent au plan historique. L’OBT validée ultérieurement consolidera les exports effectivement produits au grain du lot 4.
- **Références.** Commits `cdb0286`, `cadb884` et `eca96ea` pour le plan, `383848b` pour la mise en œuvre. [Mesures Bronze et résultats Silver](ARCHITECTURE.md#mesures-bronze-et-résultats-silver)

## Préparation du Silver et protocole du pilote

### DEC-012 · Arbitrer les quatre paires de libellés identiques

**Statut** retenue.

- **Contexte et solutions.** Le Bronze contenait quatre paires de libellés identiques et aucun doublon strict sur les six champs. Le jalon Bronze proposait de conserver les 5 299 lignes en signalant les huit variantes.
- **Choix et justification.** Garder une seule ligne par paire pour donner le même poids à chaque libellé. Retenir la catégorie jeux vidéo pour Pokémon, les distracteurs numériques plus proches pour l’heptagone, l’année 1789 pour la question formulée à l’année et Michel-Ange comme distracteur plus plausible pour la Joconde.
- **Conséquences et limites.** Le premier dédoublonnage ramène Silver de 5 299 à 5 295 lignes. Le Bronze et le Parquet de conversion gardent les variantes. DEC-019 traite les différences résiduelles de forme avec une clé de comparaison plus large.
- **Références.** Commits `cadb884` et `4c63216`. [Arbitrages et rangs Bronze](CURRENT.md#dédoublonnage-silver)

### DEC-013 · Normaliser les champs texte et typer les distracteurs

**Statut** retenue · **Validation** 24 novembre 2026.

- **Contexte.** Le jalon dédoublonné conserve encore les entités HTML et la liste de distracteurs sous forme de texte JSON.
- **Choix et justification.** Décoder les entités HTML, convertir les distracteurs en liste, appliquer Unicode NFC, retirer les espaces périphériques et réduire les espaces ordinaires répétés. Conserver les espaces insécables isolés, les signes `+` et l’ordre des distracteurs source.
- **Conséquences et limites.** Le Parquet normalisé conserve 5 295 lignes et six champs, dont une liste de chaînes. Le diagnostic a relevé zéro séquence `%HH` à décoder. Les corrections de langue et l’ordre d’affichage des choix relèvent de DEC-015 et DEC-016.
- **Références.** Commit `4c63216`. [Normalisation validée](CURRENT.md#étapes-2-à-5-de-silver-validées) · [Implémentation](../preparer_silver.py)

### DEC-014 · Tester un premier manifeste sur le jalon dédoublonné

**Statut** remplacée par DEC-018 pour le pilote mesuré.

- **Contexte.** Un essai vérifie la préparation des choix et le tirage stratifié sur le jalon dédoublonné avant la finalisation du corpus.
- **Choix et justification.** Garder `questions_benchmark.parquet` et `data/silver/pilot_question_ids.parquet` comme traces provisoires. Le tirage de 530 questions permet de vérifier l’allocation des strates et la reproductibilité sous permutation des lignes.
- **Conséquences et évolution.** L’essai est déclaré invalide pour le benchmark final. Le manifeste expérimental validé est construit ensuite à partir du Silver enrichi et publié dans un autre répertoire (DEC-018).
- **Références.** Commits `4c63216`, `907fbb6` et `383848b`. [Essai provisoire](CURRENT.md#constats-sur-lessai-provisoire) · [Protocole historique](../README.md#protocole-historique-du-pilote-gemma)

### DEC-015 · Garder les questions en anglais et limiter les corrections de langue

**Statut** retenue · **Validation du candidat** 24 novembre 2026.

- **Contexte et solutions.** Le diagnostic du corpus anglais combine une relecture et Hunspell avec les dictionnaires américain et britannique, complétés par LanguageTool 6.6. Il distingue corrections groupables, cas individuels et reformulations stylistiques hors périmètre.
- **Choix et justification.** Conserver la langue des questions et des choix. Appliquer uniquement les huit modifications prioritaires validées, soit six libellés et deux bonnes réponses. L’arbitrage limite les changements de sens et rend chaque intervention vérifiable par identifiant de proposition, champ, texte d’origine et empreinte.
- **Conséquences et limites.** Le candidat publié contient 5 295 lignes × 10 colonnes. Le rapport conserve les choix laissés en l’état et les limites, dont certaines ambiguïtés de référence. La conservation de l’anglais est attestée par les artefacts. Une validation séparée de la langue et une comparaison avec une traduction ne figurent pas dans les sources.
- **Références.** Commits `eca96ea` et `907fbb6`. [Diagnostic linguistique](CURRENT.md#diagnostic-linguistique-du-lot-2) · [Arbitrage du candidat](CURRENT.md#candidat-silver-après-arbitrage) · [Rapport qualité](../data/silver/rapport_qualite_silver.csv)

### DEC-016 · Stabiliser les identifiants et figer l’ordre des choix

**Statut** retenue.

- **Contexte.** Les comparaisons et les reprises exigent des identifiants indépendants de l’ordre des lignes et des distracteurs, ainsi qu’un même ordre de présentation pour toutes les expériences.
- **Choix et justification.** Calculer `question_id` par SHA-256 du contenu normalisé avec distracteurs triés. Mélanger les choix de façon déterministe par SHA-256 du JSON `["choix", 42, question_id, réponse]` et figer le résultat dans `answer_choices`. Déduire `expected_answer` de la position A à D ou de la valeur `True` ou `False`. Associer `category_id` au catalogue OpenTDB figé dans le script pour permettre une reproduction hors ligne.
- **Conséquences et limites.** Réordonner les lignes ou les distracteurs source laisse les identifiants et l’ordre des choix stables. Une modification du contenu de référence peut changer l’identifiant. L’ordre figé contrôle l’effet de position entre conditions et le protocole ne mesure pas l’effet d’autres permutations.
- **Références.** Commits `eca96ea` et `383848b`. [Champs Silver](ARCHITECTURE.md#silver) · [Fonctions de préparation](../preparer_silver.py)

### DEC-017 · Versionner les livrables sélectionnés et garder les artefacts de travail locaux

**Statut** retenue · **Première publication documentée** 24 novembre 2026.

- **Contexte et solutions.** La collecte, les journaux et les rapports sont d’abord locaux. Le partage de livrables contrôlés permet aux lecteurs de retrouver les jalons sans relancer la collecte.
- **Choix et justification.** Publier le CSV Bronze de référence, les Parquet Silver de référence et les rapports de qualité retenus. Étendre ensuite les exceptions Git au manifeste Gemma validé, à ses métadonnées et aux exports Gemma P1/P2 sélectionnés. Ignorer par défaut les données générées, les bases et journaux DuckDB, les états de reprise, `.venv` et les secrets.
- **Conséquences et limites.** Gemma P3 et les trois exports complets Ministral restent locaux. Un clone Git seul ne fournit donc que trois des sept sources de la future OBT. Les exclusions s’appliquent aux fichiers publiés dans le dépôt, tandis que les traces locales restent disponibles pour l’audit.
- **Références.** Commits `294fb25`, `bc4cb0f`, `383848b` et `e981472`. [Fichiers publiés](../README.md#jeux-de-données-disponibles-sur-github) · [Exclusions Git](../.gitignore) · [Disponibilité des sept sources](ARCHITECTURE.md#sources-du-silver-préparé)

### DEC-018 · Valider un manifeste stratifié et reproductible pour Gemma

**Statut** retenue.

- **Contexte et solutions.** Le manifeste provisoire de DEC-014 appartient à un autre jalon. Le pilote mesuré doit comparer les prompts sur un même sous-ensemble du corpus préparé.
- **Choix et justification.** Tirer 10 % selon les strates catégorie × difficulté × type, avec arrondi au plus proche, allocation par plus forts restes et départage lexicographique. Fixer la sélection et l’ordre par SHA-256 avec la seed 42. Conserver `pilot_order`, `question_id`, la seed et les empreintes dans les fichiers du pilote validé.
- **Conséquences et limites.** Le tirage historique donne 530 questions sur 5 295 couvrant 109 des 141 strates. Les cinq exclusions ultérieures ne touchent aucun identifiant tiré. Le manifeste est conservé, avec distinction entre corpus de tirage et Silver actif de 5 290 questions.
- **Références.** Commits `907fbb6` et `383848b`. [Pilote Gemma et tirage](CURRENT.md#pilote-gemma-4-e2b-sur-le-silver-définitif) · [Métadonnées du manifeste](../data/silver/pilot_lot2/manifest_metadata.json)

### DEC-019 · Écarter cinq variantes encore détectées après normalisation

**Statut** retenue.

- **Contexte.** Après DEC-012 et DEC-015, une comparaison des libellés en NFC, sans distinction de casse, sans espaces, ponctuation ni guillemets assimilés, détecte cinq autres groupes.
- **Choix et justification.** Valider cinq couples GARDER/EXCLURE par identifiant et libellé exact. Les motifs consignés concernent les guillemets de Nephelococcygia, la ponctuation et l’orthographe de la version *Quercus robur*, la ponctuation de la planète la plus chaude, la ponctuation et la plausibilité d’un distracteur pour le plus grand pays, et la graphie sans guillemets de *The Starry Night*.
- **Conséquences et limites.** Le Silver révisé contient 5 290 lignes et aucun des cinq groupes détectés. La clé sert au repérage. Les exclusions résultent des dix décisions explicites et la version antérieure reste archivée. Le tirage déjà validé est conservé selon DEC-018.
- **Références.** Commit `383848b`. [Révision du Silver](CURRENT.md#révision-du-silver-après-les-cinq-arbitrages) · [Rapport qualité, lignes D01 à D05](../data/silver/rapport_qualite_silver.csv)

### DEC-020 · Comparer d’abord les deux prompts P1 et P2

**Statut** retenue.

- **Contexte et solutions.** Le plan P0–P3 de DEC-009 mêlait plusieurs changements de consigne. Le premier pilote isole le rôle d’expert.
- **Choix et justification.** `P1_choices` donne la question, les choix figés et l’exigence d’une lettre majuscule A à D ou de `True` ou `False`. `P2_expert` ajoute uniquement le rôle d’expert en culture générale. Utiliser les mêmes questions, le même ordre et les mêmes réglages, dans deux blocs successifs. Le pilote Gemma fixe notamment la température à 0, le contexte à 4 096 tokens et le plafond de sortie à 16 tokens.
- **Conséquences et limites.** La comparaison P1–P2 contrôle le contenu et l’ordre des choix. L’ordre fixe des blocs peut affecter la latence si la température ou la charge évolue. DEC-026 ajoute P3 tout en préservant P1 et P2.
- **Références.** Commits `eca96ea`, `383848b` et `4203835`. [Consignes et gabarits](ARCHITECTURE.md#benchmark)

### DEC-021 · Rendre les inférences indépendantes au niveau conversationnel

**Statut** retenue.

- **Contexte.** L’historique d’une conversation ou l’envoi de la réponse attendue empêcherait d’attribuer correctement la performance au modèle et au prompt.
- **Choix et justification.** Envoyer un seul texte par requête à `POST /api/v1/chat`, avec `store=false` et sans `previous_response_id`. N’envoyer que la consigne, le libellé et les choix ordonnés. Garder `expected_answer` pour le scoring local. Précéder les blocs d’un échauffement synthétique distinct des mesures.
- **Conséquences et limites.** Les journaux serveur attestent l’indépendance conversationnelle. Le protocole garde l’instance chargée entre les blocs et ne mesure pas l’état de son cache interne.
- **Références.** Commits `383848b`, `e981472`, `a855785` et `917fbe1`. [Audit conversationnel](ARCHITECTURE.md#indépendance-conversationnelle) · [Clôture Ministral](CURRENT.md#benchmark-complet-ministral-du-lot-4)

### DEC-022 · Appliquer le scoring strict et garder les réponses hors format

**Statut** retenue.

- **Contexte et solutions.** Le plan initial laissait ouvertes les règles pour `INCONNU` et les sorties hors format. Le protocole retenu impose une sortie courte et une évaluation uniforme.
- **Choix et justification.** Retirer les espaces périphériques, valider uniquement `A` à `D` pour un QCM et `True` ou `False` pour un vrai/faux, puis comparer avec `expected_answer`. Une sortie hors format garde sa réponse brute et compte comme incorrecte. Une tentative en échec technique conserve son statut et reste hors du calcul des taux sur les réponses reçues.
- **Conséquences et limites.** Exactitude et conformité utilisent comme dénominateur les réponses reçues. Une réponse contenant la lettre correcte au milieu d’une explication reste incorrecte au scoring strict. Elle reste dans les exports qui alimenteront l’OBT.
- **Références.** Commits `eca96ea` et `383848b`. [Mesures et dénominateurs](ARCHITECTURE.md#benchmark) · [Fonction de scoring](../pilote_gemma.py)

## Exécution et évolution des benchmarks

### DEC-023 · Séparer les mesures Bronze et les résultats Silver par modèle et prompt

**Statut** retenue. Cette décision remplace le schéma provisoire de DEC-011.

- **Contexte et solutions.** L’export Silver unique envisagé initialement combinait données brutes et résultats d’évaluation. La séparation devient nécessaire pour conserver les réponses observées et reconstruire leur évaluation.
- **Choix et justification.** Produire un Parquet Bronze par modèle × prompt avec réponse brute, latence, configuration, statut et diagnostics. Produire le Parquet Silver correspondant à partir du Bronze et des réponses attendues, en ajoutant `ai_answer`, `ai_correct` et `format_valid`. Conserver `inference_id` pour relier les couches et `question_id` pour relier le corpus.
- **Conséquences et limites.** Les résultats Silver peuvent être reconstruits hors ligne et contrôlés contre le Bronze. L’analyse multi-modèle requiert une consolidation explicite, traitée par DEC-032. Les Parquet restent distincts par modèle et prompt.
- **Références.** Commit `383848b`. [Champs Bronze et Silver](ARCHITECTURE.md#mesures-bronze-et-résultats-silver)

### DEC-024 · Journaliser les tentatives et sauvegarder progressivement

**Statut** retenue.

- **Contexte.** Les blocs peuvent durer longtemps ou être interrompus. Une exportation en fin de bloc laisserait une fenêtre de perte de mesures.
- **Choix et justification.** Journaliser chaque tentative dans DuckDB avant et après l’appel, avec un identifiant unique et un segment horodaté. Exporter atomiquement Bronze puis Silver toutes les 25 nouvelles tentatives et à la fin du bloc. Vérifier les empreintes et la configuration avant la reprise, puis traiter les positions absentes.
- **Conséquences et limites.** Une réception indéterminée devient `interrupted` et reste traçable. Les erreurs techniques sont conservées par catégorie. La latence HTTP est mesurée jusqu’à réception complète, avec un délai maximal de 60 s. Le temps actif inclut la persistance et les échecs, avec chargement, échauffements et pauses hors mesure. DEC-031 documente une reprise ciblée lorsque l’absence de réception côté serveur a été établie.
- **Références.** Commits `eca96ea` et `383848b`. [Journalisation et reprise](ARCHITECTURE.md#mesures-bronze-et-résultats-silver) · [Pipeline d’inférence](../pilote_gemma.py)

### DEC-025 · Réutiliser les mesures du pilote dans le benchmark complet Gemma

**Statut** retenue.

- **Contexte.** Le pilote validé dispose déjà de 530 mesures par prompt. Le passage au corpus complet doit préserver leur provenance et éviter de mesurer deux fois les mêmes positions.
- **Choix et justification.** Copier les journaux du pilote et reprendre chaque mesure compatible, y compris hors format. Fixer le manifeste complet aux 530 premiers rangs du pilote, suivis des 4 760 questions restantes dans l’ordre du Silver révisé. Vérifier la configuration avant de traiter le complément.
- **Conséquences et limites.** Les réponses, identifiants et latences du pilote sont préservés. Gemma couvre 5 290 questions par prompt. L’extension P3 (DEC-026) reprend ses propres 530 mesures sur le même manifeste. La clôture établit Gemma 4 E2B comme premier benchmark complet validé.
- **Références.** Commits `e981472` et `a855785`. [Benchmark Gemma](CURRENT.md#benchmark-gemma-du-lot-4) · [Clôture des trois prompts](CURRENT.md#comparaison-complète-des-trois-prompts)

### DEC-026 · Étendre le protocole au prompt P3 d’analyse et de vérification

**Statut** retenue. Cette décision étend DEC-020 et donne à P3 un sens différent du plan de DEC-009.

- **Contexte et solutions.** Les deux premiers prompts isolent le rôle d’expert. Le nouveau test mesure l’effet de consignes d’analyse et de vérification sur le même corpus.
- **Choix et justification.** Construire `P3_expert_advanced` à partir de P2 en ajoutant les consignes d’examen des choix ou de l’assertion, puis de vérification. Garder le format de réponse, les choix, les réglages et le scoring. Valider d’abord le bloc de 530 questions, puis mesurer les 4 760 positions restantes.
- **Conséquences et limites.** P3 est comparable aux deux premiers prompts. Gemma obtient 55 réponses P3 hors format sur le corpus complet, conservées et comptées comme incorrectes. Les consignes plus longues peuvent modifier la conformité et la latence. L’indication du domaine prévue à l’origine reste sans résultat attesté.
- **Références.** Commits `4203835` et `a855785`. [Pilote P3](CURRENT.md#pilote-de-p3_expert_advanced) · [Comparaison complète](CURRENT.md#comparaison-complète-des-trois-prompts)

### DEC-027 · Comparer la faisabilité des candidats sur les mêmes 30 questions

**Statut** retenue.

- **Contexte.** Un deuxième modèle doit pouvoir traiter le corpus sur la machine disponible et suivre le même protocole. Un essai court limite le coût de cette vérification.
- **Choix et justification.** Réserver les 30 premiers rangs du manifeste Gemma, dans leur ordre d’origine. Réutiliser les choix, les trois prompts, le scoring et les paramètres compatibles pour Bonsai, Qwen et Ministral. Observer la qualité, la conformité, les latences et la pression mémoire lorsqu’elle est mesurable.
- **Conséquences et limites.** Les pilotes comparent le même échantillon de 27 QCM et 3 vrai/faux. Les projections sont indicatives. Bonsai s’est arrêté durant P2 et son estimation historique extrapole la latence des réponses reçues. Qwen et Ministral utilisent le temps actif des trois blocs complets pour leurs projections.
- **Références.** Commits `cc0ec23`, `8005f4b` et `fb93faa`. [Manifeste commun](ARCHITECTURE.md#pilote-bonsai-27b) · [Comparaison des trois pilotes](CURRENT.md#comparaison-des-trois-tests-de-faisabilité)

### DEC-028 · Évaluer Bonsai 27B comme deuxième modèle

**Statut** abandonnée.

- **Contexte.** Bonsai 27B Q1_0 a été testé comme deuxième modèle sur la machine du projet.
- **Arbitrage et justification.** Arrêter le pilote après 41 réponses et écarter le benchmark complet en raison de la pression mémoire et du temps extrapolé. L’estimation historique donne environ 67 h 05 de temps d’inférence pour les trois prompts, calculée à partir des réponses observées.
- **Conséquences et limites.** P1 est complet, P2 est partiel et sa douzième tentative est archivée comme interrompue. P3 est resté au stade de la préparation. Les résultats conservés localement servent à la traçabilité et restent hors du périmètre final.
- **Références.** Commit `cc0ec23` du 24 novembre 2026. [Fin du pilote Bonsai](CURRENT.md#pilote-bonsai-27b-arrêté-et-modèle-abandonné) · [Relevés mémoire](../data/silver/pilote_bonsai/memoire.jsonl)

### DEC-029 · Évaluer Qwen3 4B Instruct comme deuxième modèle

**Statut** abandonnée · **Arbitrage final** 25 novembre 2026.

- **Contexte et solutions.** Qwen3-4B-Instruct-2507 Q4_K_M succède à Bonsai comme candidat. Le pilote de 90 inférences est validé et le benchmark complet reste d’abord en attente d’arbitrage.
- **Arbitrage et justification.** Écarter Qwen lors de la sélection de Ministral. Qwen a une durée active extrapolée de 7 h 52 min sur le benchmark complet et son P3 a donné zéro réponse conforme sur 30. Le choix de la variante Instruct, sans réglage de réflexion, reste documenté pour la reproduction du pilote.
- **Conséquences et limites.** Les 90 résultats et les 31 réponses hors format restent conservés dans les fichiers du pilote. Le P3 de ce pilote est mesuré sur l’échantillon commun. Qwen reste hors du périmètre final de DEC-032.
- **Références.** Commits `8005f4b` et `fb93faa`. [Pilote Qwen](CURRENT.md#test-de-faisabilité-qwen3-4b-instruct-2507) · [Choix du deuxième modèle](CURRENT.md#choix-définitif-du-deuxième-modèle)

### DEC-030 · Retenir Ministral comme deuxième modèle complet

**Statut** retenue · **Validation du choix** 25 novembre 2026.

- **Contexte et solutions.** Les pilotes de Bonsai, Qwen et Ministral permettent de comparer leur faisabilité sur le poste et le respect du format.
- **Choix et justification.** Sélectionner Ministral-3-3B-Instruct-2512 Q4_K_M comme deuxième modèle, avec un contexte de 4 096 tokens, Vulkan 2.80.1 et une limite de 16 tokens de sortie. C’est le compromis validé entre durée, conformité et contraintes matérielles. Le pilote termine ses 90 inférences, avec 73,3 % de conformité P3 et une durée complète extrapolée de 4 h 52 min.
- **Conséquences et limites.** Reprendre ses 90 mesures du pilote, conserver le manifeste complet de Gemma et ajouter 5 260 inférences par prompt, selon DEC-025. L’instance doit être rechargée à l’identique et le scoring reste strict. La conformité P3 du pilote reste inférieure à celle des deux premiers prompts.
- **Références.** Commits `fb93faa` et `917fbe1`. [Sélection de Ministral](CURRENT.md#choix-définitif-du-deuxième-modèle) · [Configuration du pilote](ARCHITECTURE.md#pilote-ministral-3-3b-instruct-2512)

### DEC-031 · Archiver les échecs de transport avérés et reprendre les positions non reçues

**Statut** retenue · **Incident et reprise** 25 novembre 2026.

- **Contexte.** Le client HTTP interrompt P3 de Ministral après 3 159 réponses reçues, pilote inclus. Treize tentatives en échec suivent la dernière réponse reçue.
- **Arbitrage et justification.** Rapprocher le journal DuckDB avec les requêtes LM Studio pour établir que ces positions sont restées côté client. Archiver les treize lignes dans `echecs_transport_reprise`, avec leurs identifiants, puis libérer uniquement leurs positions pour la reprise. Resélectionner Vulkan 2.80.1 et recharger la configuration du pilote.
- **Conséquences et limites.** Les 13 739 réponses déjà reçues sont conservées, y compris les sorties hors format. La reprise complète les 2 131 positions restantes de P3. L’archive fait partie de l’audit et reste hors des six ensembles finaux. Cette exception documentée à la reprise ordinaire de DEC-024 repose sur la preuve de non-réception côté serveur. Le benchmark Ministral et son comparatif avec Gemma ont depuis été validés et le lot 4 est clos.
- **Références.** Commit `917fbe1`. [Clôture du benchmark](CURRENT.md#benchmark-complet-ministral-du-lot-4) · [Journal d’exécution](../data/silver/benchmark_ministral_lot4/execution.log) · [Synthèse d’audit](../data/silver/benchmark_ministral_lot4/verification.json)

## Consolidation Silver et préparation de Gold

### DEC-032 · Construire une One Big Table dans le Silver consolidé

**Statut** retenue.

- **Contexte.** Les six exports complets validés de DEC-023 et le corpus OpenTDB sont disponibles séparément. Les comparaisons appariées et les agrégations réutilisent les mêmes jointures et le même grain.
- **Choix et justification.** Faire lire et typer les sept Parquet par `staging`. Construire l’OBT en DuckDB via `intermediate`, avec `UNION ALL` des six benchmarks puis `JOIN` au corpus sur `question_id`. Garder une ligne par question × modèle × prompt. Conserver les identifiants réels, le scoring strict, les statuts et les latences pour permettre la traçabilité et des indicateurs cohérents.
- **Conséquences et limites.** Le grain donne 31 740 lignes attendues pour 5 290 questions distinctes. Les attributs OpenTDB sont répétés six fois par question. Les réponses hors format restent incluses. Les pilotes Bonsai et Qwen et les échecs archivés restent hors du périmètre. Les marts dbt produiront les jeux Gold issus de l’OBT, puis Streamlit consommera ces jeux. La validation porte sur l’architecture cible. L’OBT reste à construire.
- **Références.** [Décision validée et état](CURRENT.md#consolidation-silver-validée) · [Sources et granularité](ARCHITECTURE.md#sources-du-silver-préparé) · [Gold et restitution](ARCHITECTURE.md#gold-et-restitution)

### DEC-033 · Préciser le modèle relationnel et le dictionnaire Gold

**Statut** proposée.

- **Contexte.** Le système cible délimite le Silver consolidé et les marts Gold (DEC-032). Le détail des produits analytiques reste à arbitrer.
- **Proposition et justification.** Préciser le modèle relationnel et le dictionnaire des données Gold. La documentation en vigueur les mentionne comme travaux ouverts et ne consigne aucun schéma détaillé validé.
- **Conséquences et limites.** Les mesures déjà définies par le protocole constituent la référence pour le futur dictionnaire. Les choix de tables, relations et granularités Gold restent à valider. Aucune variante détaillée de modèle Gold n’est documentée.
- **Références.** Décision ouverte dès `cadb884`. [Choix à arbitrer](ARCHITECTURE.md#choix-à-arbitrer) · [Mesures](ARCHITECTURE.md#benchmark)

## Informations manquantes et écarts entre les sources

- **Motifs et dates d’adoption.** Le choix initial de Gemma, le choix de LM Studio et le maintien de l’anglais sont attestés par les documents ou les artefacts. Les sources ne donnent pas toujours de date d’accord distincte, de comparaison d’alternatives ou de justification spécifique. La date exacte de validation de l’OBT n’est pas consignée séparément dans les documents de référence.
- **Effectifs du rapport qualité.** Le diagnostic et le classement comptent chacun 1 030 entrées. L’ajout de cinq propositions d’arbitrage donne 1 035 entrées pour le candidat historique, puis les dix lignes GARDER/EXCLURE portent le rapport révisé à 1 045. Ces volumes correspondent aux étapes documentées. L’écart résiduel accepté lors de la première publication est mentionné sans détail permettant d’en identifier la nature exacte. [Publication du Silver](CURRENT.md#publication-du-silver-définitif) · [Rapport révisé](../data/silver/rapport_qualite_silver.csv)
- **Périmètre des prompts.** Les consignes aux agents parlent de P1 et P2 dans la section consacrée au pilote. L’historique et les résultats finaux attestent trois prompts pour le lot 4. Les libellés P1, P2 et P3 du premier README désignent aussi des variantes différentes. Les décisions DEC-009, DEC-020 et DEC-026 relient ces états. [Consignes de pilote](../AGENTS.md#pilote-du-benchmark) · [Clôture du lot 4](CURRENT.md#clôture-du-lot-4)
- **Mesures prévues et mesures produites.** La stabilité des réponses figure parmi les axes initiaux. Les mesures finales et leurs audits décrivent une réponse par question, modèle et prompt. Aucun ensemble de répétitions dédié à la stabilité n’est attesté. [Protocole](ARCHITECTURE.md#benchmark) · [Comparatif final](CURRENT.md#comparaison-avec-gemma)
