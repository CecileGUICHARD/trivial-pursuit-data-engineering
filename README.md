# Trivial Pursuit · Benchmark de LLM locaux

Projet du cours D42, ETL et optimisation des architectures de stockage, en M1 Big Data & IA (23 au 26 novembre 2026).

Le projet construit un pipeline reproductible et traçable pour collecter des questions de culture générale, préparer les données et comparer des modèles de langage exécutés localement. Le benchmark sert de cas d’usage pour démontrer la maîtrise de la collecte, des contrôles qualité, de la transformation, de la modélisation, du stockage, de l’automatisation et de la restitution.

Les livrables attendus sont le dépôt GitHub, une application Streamlit et une présentation orale. La collecte Bronze a été réalisée et peut être explorée à partir du CSV local. Le [suivi d’avancement](documentation/CURRENT.md) précise les étapes réalisées et les prochaines étapes.

## Source des données

Open Trivia Database fournit une API JSON publique sans clé, sous licence CC BY-SA 4.0. Elle autorise jusqu’à 50 questions par appel, avec un intervalle de 5 secondes entre deux appels d’une même adresse IP. Les jetons de session permettent à l’API de suivre les questions déjà renvoyées pendant la collecte. [Documentation OpenTDB](https://opentdb.com/api_config.php)

## Installation sous Debian (WSL)

Depuis la racine du dépôt, créer l’environnement virtuel s’il est absent, puis l’activer. Les scripts de collecte utilisent `requests`. Le pilote et l’exploration utilisent aussi `pandas`.

```bash
test -d .venv || python3 -m venv .venv
source .venv/bin/activate
python -m pip install requests pandas
```

## Utilisation

### Examiner la collecte existante

Si le CSV local `data/bronze/questions_raw.csv` est présent, lancer depuis la racine du dépôt.

```bash
python exploration.py
```

Le script affiche la volumétrie, la complétude, les répartitions et les questions aux libellés répétés. Les fichiers de données et l’état de reprise restent locaux.

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

La commande écrit le Parquet candidat et le rapport qualité dans `data/silver/candidat_final/`. Le lot 2 validé est publié dans `data/silver/questions_clean.parquet`, avec `data/silver/rapport_qualite_silver.csv`. [Publication du Silver définitif](documentation/CURRENT.md#publication-du-silver-définitif)

### Pilote après validation

La commande historique `preparer_silver.py pilote` reste suspendue. Les deux fichiers suivants proviennent de l’essai antérieur à la finalisation.

| Fichier Silver | Contenu |
| --- | --- |
| `questions_benchmark.parquet` | 5 295 questions normalisées, identifiants stables, propositions ordonnées et lettres attendues |
| `pilot_question_ids.parquet` | 530 identifiants tirés avec la seed 42 par catégorie, difficulté et type, dans l’ordre du pilote |

Le pilote utilisera Gemma 4 E2B via LM Studio sur les mêmes questions avec `P1_choices` (une lettre pour un QCM, `True` ou `False` pour un vrai/faux) et `P2_expert` (mêmes consignes, avec ajout du rôle d’expert en culture générale). Les réponses réelles seront conservées dans Silver et serviront au calcul de la précision, des latences, du respect du format, des erreurs techniques et de la durée. La durée observée servira à estimer le temps à prévoir par prompt. La validation de l’utilisatrice est requise avant le benchmark complet ou le choix d’un deuxième modèle. [Protocole détaillé](documentation/ARCHITECTURE.md#benchmark)

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

- `data/` accueille les couches Bronze, Silver et Gold.
- `dbt/` accueille les modèles SQL et leurs tests. `app/` est réservé à la restitution Streamlit.
- La [référence technique](documentation/ARCHITECTURE.md) détaille les flux, les formats et le benchmark.
- Les [consignes pour les agents IA](AGENTS.md) décrivent les règles de collaboration.
