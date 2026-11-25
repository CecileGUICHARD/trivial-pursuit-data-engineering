# Trivial Pursuit · Benchmark de LLM locaux

Projet du cours D42, ETL et optimisation des architectures de stockage, en M1 Big Data & IA (23 au 26 novembre 2026).

Le projet construit un pipeline reproductible et traçable pour collecter des questions de culture générale, préparer les données et comparer des modèles de langage exécutés localement. Le benchmark sert de cas d’usage pour démontrer la maîtrise de la collecte, des contrôles qualité, de la transformation, de la modélisation, du stockage, de l’automatisation et de la restitution.

Le dépôt GitHub et la présentation orale documentent le projet. Les futurs marts Gold serviront à la consommation dans Power BI, Qlik, un environnement de data science ou une application métier. [Suivi d’avancement](documentation/CURRENT.md) · [Registre des décisions](documentation/DECISIONS.md)

## Architecture des données

| Couche | Rôle et état |
| --- | --- |
| Bronze | Données brutes OpenTDB et LLM conservées intactes. |
| Silver | Sept Parquet validés, préparés par les scripts Python du projet. Le corpus OpenTDB contient 5 290 lignes × 10 colonnes. Les benchmarks Gemma 4 E2B et Ministral 3 3B Instruct fournissent un Parquet de 5 290 réponses par modèle et par prompt P1, P2 et P3. |
| dbt `staging` et `intermediate` | `staging` expose les sept sources avec leurs types. `intermediate` réunit les six benchmarks par `UNION ALL BY NAME`, puis les joint au corpus par `question_id`. L’OBT détaillée est matérialisée en `intermediate.obt_silver`. |
| Gold | Marts métier à construire dans le schéma DuckDB `gold`. |
| Consommation | Les futurs marts alimenteront Power BI, Qlik, la data science ou une application métier. |

L’OBT contient une ligne par question × modèle × prompt, soit **31 740 lignes, 22 colonnes et 5 290 questions distinctes**. L’identifiant de question permet les comparaisons appariées. Les identifiants source, les scores stricts, les statuts et les latences sont conservés, y compris pour les réponses hors format. Les pilotes Bonsai et Qwen et les échecs de transport archivés restent hors de ce périmètre. [Sources Silver et dictionnaire](documentation/ARCHITECTURE.md#sources-du-silver-préparé)

## Jeux de données disponibles sur GitHub

Télécharger les fichiers ci-dessous depuis GitHub pour les utiliser directement, sans relancer la collecte ni la préparation Silver.

| Fichier | Rôle et statut | Taille |
| --- | --- | ---: |
| [`data/bronze/questions_raw.csv`](data/bronze/questions_raw.csv) | Collecte OpenTDB de référence, 5 299 questions et 6 champs bruts | 895 318 octets |
| [`data/silver/questions_avant_dedoublonnage.parquet`](data/silver/questions_avant_dedoublonnage.parquet) | Jalon de conversion au format Parquet. Conserve les 5 299 lignes et les 6 champs bruts du CSV. | 429 316 octets |
| [`data/silver/questions_dedoublonnees.parquet`](data/silver/questions_dedoublonnees.parquet) | Jalon dédoublonné selon les quatre arbitrages validés, 5 295 questions et 6 champs bruts | 429 259 octets |
| [`data/silver/questions_normalisees.parquet`](data/silver/questions_normalisees.parquet) | Jalon normalisé validé, 5 295 questions et 6 champs. Les réponses incorrectes sont stockées sous forme de liste. | 424 385 octets |
| [`data/silver/questions_clean.parquet`](data/silver/questions_clean.parquet) | Corpus du benchmark révisé, 5 290 questions et 10 colonnes après les cinq exclusions validées. Intègre les huit corrections historiques et quatre champs d’enrichissement. | 966 677 octets |
| [`data/silver/diagnostic_anglais_lot2.csv`](data/silver/diagnostic_anglais_lot2.csv) | Diagnostic linguistique du jalon normalisé, avec 1 019 propositions de correction et 11 cas à éclaircir | 334 495 octets |
| [`data/silver/classement_diagnostic_anglais_lot2.csv`](data/silver/classement_diagnostic_anglais_lot2.csv) | Classement des 1 030 entrées du diagnostic par catégorie, risque et modalité de validation, utilisé pour préparer l’arbitrage | 600 327 octets |
| [`data/silver/rapport_qualite_silver.csv`](data/silver/rapport_qualite_silver.csv) | Rapport de 1 045 entrées avec les décisions historiques et les dix lignes GARDER/EXCLURE des cinq groupes. | 822 814 octets |
| [`data/bronze/gemma_p1_choices.parquet`](data/bronze/gemma_p1_choices.parquet) | 530 tentatives brutes de Gemma 4 E2B pour `P1_choices` | 54 301 octets |
| [`data/bronze/gemma_p2_expert.parquet`](data/bronze/gemma_p2_expert.parquet) | 530 tentatives brutes de Gemma 4 E2B pour `P2_expert` | 54 296 octets |
| [`data/silver/gemma_p1_choices.parquet`](data/silver/gemma_p1_choices.parquet) | 530 résultats structurés pour `P1_choices` | 52 550 octets |
| [`data/silver/gemma_p2_expert.parquet`](data/silver/gemma_p2_expert.parquet) | 530 résultats structurés pour `P2_expert` | 52 545 octets |
| [`data/silver/pilot_lot2/pilot_question_ids.parquet`](data/silver/pilot_lot2/pilot_question_ids.parquet) | Manifeste définitif des 530 questions du pilote | 38 037 octets |
| [`data/silver/pilot_lot2/manifest_metadata.json`](data/silver/pilot_lot2/manifest_metadata.json) | Empreintes du manifeste, du corpus de tirage et du Silver révisé | 991 octets |
| [`data/bronze/benchmark_lot4/gemma_p1_choices.parquet`](data/bronze/benchmark_lot4/gemma_p1_choices.parquet) | 5 290 mesures brutes du benchmark complet pour `P1_choices` | 502 851 octets |
| [`data/bronze/benchmark_lot4/gemma_p2_expert.parquet`](data/bronze/benchmark_lot4/gemma_p2_expert.parquet) | 5 290 mesures brutes du benchmark complet pour `P2_expert` | 502 846 octets |
| [`data/bronze/benchmark_lot4/gemma_p3_expert_advanced.parquet`](data/bronze/benchmark_lot4/gemma_p3_expert_advanced.parquet) | 5 290 mesures brutes Gemma pour `P3_expert_advanced` | 506 618 octets |
| [`data/silver/benchmark_lot4/gemma_p1_choices.parquet`](data/silver/benchmark_lot4/gemma_p1_choices.parquet) | 5 290 résultats structurés du benchmark complet pour `P1_choices` | 484 464 octets |
| [`data/silver/benchmark_lot4/gemma_p2_expert.parquet`](data/silver/benchmark_lot4/gemma_p2_expert.parquet) | 5 290 résultats structurés du benchmark complet pour `P2_expert` | 484 459 octets |
| [`data/silver/benchmark_lot4/gemma_p3_expert_advanced.parquet`](data/silver/benchmark_lot4/gemma_p3_expert_advanced.parquet) | 5 290 résultats structurés Gemma pour `P3_expert_advanced` | 488 586 octets |
| [`data/bronze/benchmark_ministral_lot4/ministral_p1_choices.parquet`](data/bronze/benchmark_ministral_lot4/ministral_p1_choices.parquet) | 5 290 mesures brutes Ministral pour `P1_choices` | 503 784 octets |
| [`data/bronze/benchmark_ministral_lot4/ministral_p2_expert.parquet`](data/bronze/benchmark_ministral_lot4/ministral_p2_expert.parquet) | 5 290 mesures brutes Ministral pour `P2_expert` | 503 972 octets |
| [`data/bronze/benchmark_ministral_lot4/ministral_p3_expert_advanced.parquet`](data/bronze/benchmark_ministral_lot4/ministral_p3_expert_advanced.parquet) | 5 290 mesures brutes Ministral pour `P3_expert_advanced` | 522 994 octets |
| [`data/silver/benchmark_ministral_lot4/ministral_p1_choices.parquet`](data/silver/benchmark_ministral_lot4/ministral_p1_choices.parquet) | 5 290 résultats structurés Ministral pour `P1_choices` | 485 512 octets |
| [`data/silver/benchmark_ministral_lot4/ministral_p2_expert.parquet`](data/silver/benchmark_ministral_lot4/ministral_p2_expert.parquet) | 5 290 résultats structurés Ministral pour `P2_expert` | 486 125 octets |
| [`data/silver/benchmark_ministral_lot4/ministral_p3_expert_advanced.parquet`](data/silver/benchmark_ministral_lot4/ministral_p3_expert_advanced.parquet) | 5 290 résultats structurés Ministral pour `P3_expert_advanced` | 505 538 octets |

Les trois CSV de qualité utilisent le point-virgule comme séparateur. Le diagnostic et son classement documentent les propositions. Le rapport définitif indique celles qui ont été appliquées.

Un clone du dépôt contient les douze Parquet définitifs des benchmarks. Les six exports Silver totalisent 31 740 résultats et fournissent, avec le corpus OpenTDB final, toutes les sources du build dbt. Les journaux DuckDB de reprise, le manifeste d’exécution du lot 4, l’essai historique, les copies du candidat final et les fichiers temporaires restent locaux. [Chemins des sources Silver validées](documentation/ARCHITECTURE.md#sources-du-silver-préparé)

## Source des données

Open Trivia Database fournit une API JSON publique sans clé, sous licence CC BY-SA 4.0. Elle autorise jusqu’à 50 questions par appel, avec un intervalle de 5 secondes entre deux appels d’une même adresse IP. Les jetons de session permettent à l’API de suivre les questions déjà renvoyées pendant la collecte. [Documentation OpenTDB](https://opentdb.com/api_config.php)

Les questions et réponses sont créditées à Open Trivia Database et à ses contributeurs. Les jeux Bronze et Silver et les extraits de ces données dans les rapports sont redistribués sous CC BY-SA 4.0. Bronze conserve les valeurs brutes de l’API. Les jalons Silver documentent la conversion en Parquet, le dédoublonnage, la normalisation, les corrections et l’enrichissement pour le benchmark. En cas de redistribution, conserver l’attribution et le lien vers la licence, signaler les modifications et partager les adaptations sous les mêmes conditions. [Source OpenTDB](https://opentdb.com/api_config.php) · [Licence CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)

## Installation sous Debian (WSL)

Depuis la racine du dépôt, créer l’environnement virtuel s’il est absent, puis l’activer. Les scripts de collecte utilisent `requests`. Le pilote et l’exploration utilisent aussi `pandas`.

```bash
test -d .venv || python3 -m venv .venv
source .venv/bin/activate
python -m pip install requests pandas
```

## Utilisation

### Construire et documenter l’OBT intermédiaire

Un clone à jour fournit les sept Parquet validés aux chemins utilisés par le projet dbt. Le profil utilise des chemins relatifs à `dbt/`. Depuis la racine du dépôt, avec la `.venv` créée à l’étape d’installation, installer les versions épinglées et lancer les commandes ci-dessous. [Chemins des sept sources](documentation/ARCHITECTURE.md#sources-du-silver-préparé)

```bash
.venv/bin/python -m pip install -r dbt/requirements.txt
(
  cd dbt &&
  ../.venv/bin/dbt build --profiles-dir . &&
  cp target/run_results.json target/build_run_results.json &&
  ../.venv/bin/dbt docs generate --profiles-dir . --static
)
```

Le build lit les Parquet et écrit les vues `staging`, la vue d’union et la table `intermediate.obt_silver` dans `data/trivial_pursuit.duckdb`. La base `data/silver/obt_silver.duckdb` porte la table de référence du jalon précédent. Pour consulter le lignage, ouvrir `dbt/target/static_index.html`, rechercher `obt_silver` et ouvrir **Lineage Graph**. La page montre aussi le catalogue des colonnes et les tests. Les fichiers générés sous `dbt/target/` restent locaux. [Documentation dbt](https://docs.getdbt.com/reference/commands/cmd-docs) · [Dictionnaire de l’OBT](documentation/ARCHITECTURE.md#dictionnaire-des-colonnes-de-lobt)

### Examiner la collecte existante

Depuis la racine du dépôt, lancer l’exploration du CSV Bronze versionné.

```bash
python exploration.py
```

Le script affiche la volumétrie, la complétude, les répartitions et les questions aux libellés répétés.

### Préparer les questions Silver

Avec `.venv` activé, installer DuckDB et convertir le CSV Bronze depuis la racine du dépôt.

```bash
python -m pip install duckdb
python preparer_silver.py convertir
```

La conversion écrit `data/silver/questions_avant_dedoublonnage.parquet` avec toutes les lignes du CSV et les six champs bruts.

Lancer ensuite le dédoublonnage quand le Parquet de conversion est prêt.

```bash
python preparer_silver.py dedoublonner
```

Cette étape lit le Parquet de conversion, applique les arbitrages validés et écrit `data/silver/questions_dedoublonnees.parquet`. Pour enchaîner les deux étapes, lancer `python preparer_silver.py`. [Arbitrages de dédoublonnage](documentation/CURRENT.md#dédoublonnage-silver)

### Produire le candidat Silver

À partir de `questions_normalisees.parquet` et du classement linguistique, lancer depuis la racine du dépôt.

```bash
python preparer_silver.py finaliser
```

La commande reproduit le Parquet candidat et le rapport qualité dans `data/silver/candidat_final_5290/`. Les dix couples identifiant–libellé sont vérifiés avant exclusion. `python preparer_silver.py controler-doublons` contrôle en lecture seule le corpus courant `data/silver/questions_clean.parquet`. [Révision du Silver](documentation/CURRENT.md#révision-du-silver-après-les-cinq-arbitrages)

### Protocole historique du pilote Gemma

La commande historique `preparer_silver.py pilote` reste suspendue. Les deux fichiers suivants proviennent de l’essai antérieur à la finalisation.

| Fichier Silver | Contenu |
| --- | --- |
| `questions_benchmark.parquet` | 5 295 questions normalisées, identifiants stables, propositions ordonnées et lettres attendues |
| `pilot_question_ids.parquet` | 530 identifiants tirés avec la seed 42 par catégorie, difficulté et type, dans l’ordre du pilote |

Les trois prompts utilisent les mêmes 530 questions, toutes issues du Silver révisé. Pour vérifier le manifeste et reproduire les résultats Silver historiques de `P1_choices` et `P2_expert` à partir des Parquet Bronze, lancer avec `.venv` activé.

```bash
python pilote_gemma.py manifeste
python pilote_gemma.py structurer
```

Ces commandes fonctionnent hors ligne avec les fichiers versionnés. Avec le journal local, `python pilote_gemma.py reconstruire-bronze` reproduit aussi les exports Bronze et `python pilote_gemma.py bilan` affiche les métriques et les durées actives.

Pour une collecte autorisée ou une reprise, démarrer le serveur local LM Studio et relever sa version et le moteur sélectionné. Le script détecte Gemma 4 E2B et le charge à 4 096 tokens si aucune instance de ce modèle n’est chargée. Si une instance utilise déjà un autre contexte, charger une instance dédiée à 4 096 tokens avec `lms load google/gemma-4-e2b --identifier gemma-pilote-lot3 --context-length 4096`.

```bash
python pilote_gemma.py executer --lm-studio-version '0.4.28+2' \
  --runtime 'llama.cpp-win-x86_64-vulkan-avx2@2.80.1'
```

Adapter les versions à l’installation utilisée. Avec le serveur Windows et le client WSL, ajouter `--curl /mnt/c/Windows/System32/curl.exe` si le port est accessible côté Windows uniquement. La reprise réutilise le journal local et la même configuration. Chaque export périodique enregistre d’abord le Bronze, puis produit le Silver correspondant. Le lot 4 et le choix de Ministral comme deuxième modèle ont été validés. [Protocole détaillé](documentation/ARCHITECTURE.md#benchmark) · [Clôture du lot 4](documentation/CURRENT.md#clôture-du-lot-4)

### Benchmark complet Gemma du lot 4

Le benchmark complet de Gemma 4 E2B couvre les **5 290 mêmes questions pour chacun des trois prompts**. Chaque prompt réutilise 530 mesures du pilote et ajoute 4 760 nouvelles mesures. Les Parquet Silver sont lisibles dans DuckDB et alimentent l’OBT. [Comparatif Gemma–Ministral](documentation/CURRENT.md#comparaison-avec-gemma)

| Mesure | `P1_choices` | `P2_expert` | `P3_expert_advanced` |
| --- | ---: | ---: | ---: |
| Réponses correctes | 2 863 (54,12 %) | 2 852 (53,91 %) | 2 753 (52,04 %) |
| Réponses conformes | 5 290 (100 %) | 5 290 (100 %) | 5 235 (98,96 %) |
| Erreurs techniques | 0 | 0 | 0 |
| Latence moyenne | 0,463 s | 0,466 s | 0,522 s |
| Latence médiane | 0,448 s | 0,445 s | 0,491 s |
| Durée active avec le pilote | 49 min 49 s | 51 min 35 s | 55 min 41 s |

Les commandes ci-dessous documentent la préparation et l’exécution à partir du journal local. `P1_choices` puis `P2_expert` ont traité les questions restantes dans l’ordre du Silver révisé. P3 a repris le même ordre lors de son propre bloc. [Bilan détaillé](documentation/CURRENT.md#comparaison-complète-des-trois-prompts)

```bash
python benchmark_gemma.py preparer
python benchmark_gemma.py verifier --lm-studio-version '0.4.28+2' \
  --runtime 'llama.cpp-win-x86_64-vulkan-avx2@2.80.1'
python benchmark_gemma.py executer --lm-studio-version '0.4.28+2' \
  --runtime 'llama.cpp-win-x86_64-vulkan-avx2@2.80.1'
```

Sous WSL avec LM Studio sur Windows, passer les chemins de `lms.exe` et `curl.exe` via `--lms` et `--curl`. L’exécution vérifie la configuration et le moteur avant chaque reprise. `python benchmark_gemma.py bilan` lit les indicateurs du journal local lorsque celui-ci est fermé.

La reprise P3 utilise le manifeste complet du lot 4 et les 530 mesures de son propre pilote. Les Parquet P3 complets sont versionnés sous le nom `gemma_p3_expert_advanced.parquet` dans `data/bronze/benchmark_lot4/` et `data/silver/benchmark_lot4/`.

```bash
python benchmark_gemma.py executer --p3 --lm-studio-version '0.4.28+2' \
  --runtime 'llama.cpp-win-x86_64-vulkan-avx2@2.80.1' --lms lms.exe --curl curl.exe
python benchmark_gemma.py bilan --p3
```

### Reproduire la collecte dans un répertoire dédié

Les deux scripts de collecte écrivent dans `data/bronze/questions_raw.csv`. Utiliser une copie des scripts dans un répertoire distinct pour préserver la collecte d’origine. Avec `.venv` activé, exécuter depuis la racine du dépôt.

```bash
repertoire_collecte="$(mktemp -d)" &&
cp collect_opentdb.py collect_opentdb_complet.py exploration.py "$repertoire_collecte/" &&
(cd "$repertoire_collecte" && python collect_opentdb.py)
```

Pour poursuivre avec la collecte complète, rester dans la même session de terminal. Le script complet sauvegarde le pilote dans `questions_test_50.csv`, puis écrit le CSV complet et conserve un état de reprise local.

```bash
(cd "${repertoire_collecte:?Répertoire de collecte requis}" &&
 python collect_opentdb_complet.py && python exploration.py)
```

## Organisation du dépôt

- `data/bronze/` conserve les données brutes. Les sept Parquet définitifs de `data/silver/` constituent les sources Silver du build. `data/trivial_pursuit.duckdb` reçoit les modèles dbt locaux.
- `dbt/models/staging/` lit et harmonise les sources Silver. `dbt/models/intermediate/` contient l’union des benchmarks et l’OBT détaillée. `dbt/models/marts/` est réservé aux marts Gold. `dbt/tests/` contient les contrôles SQL.
- `app/` est réservé à une éventuelle application métier consommant les marts Gold.
- La [référence technique](documentation/ARCHITECTURE.md) détaille les flux, les formats et le benchmark.
- Les [consignes pour les agents IA](AGENTS.md) décrivent les règles de collaboration.
