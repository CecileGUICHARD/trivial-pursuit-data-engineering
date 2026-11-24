# État d’avancement

Mis à jour le 24 novembre 2026. L’utilisatrice a validé le lot 1 de Silver et les transformations des étapes 2 à 5 (décodage, conversion des listes, NFC et espaces). Le fichier `data/silver/questions_normalisees.parquet` (5 295 lignes × 6 colonnes) constitue le nouveau jalon Silver validé et servira de base au lot 2. Le pilote généré au cours de l’essai est provisoire et invalide pour le benchmark final. Aucune inférence n’a été lancée.

## Travail réalisé

- Debian sous WSL, VS Code et `.venv` opérationnels. Le dépôt GitHub a été initialisé avec le commit `cdb0286` (« Initialisation du projet et extraction Bronze »).
- Le pilote du 23 novembre a collecté 50 questions sur 15 catégories, dont 43 QCM et 7 questions vrai/faux. Il compte 15 questions faciles, 19 intermédiaires et 16 difficiles. Les six champs sont renseignés et les libellés sont uniques. Le CSV pilote est conservé localement dans `data/bronze/questions_test_50.csv`. Il sert à vérifier le fonctionnement de la collecte.
- La collecte complète du 23 novembre est conservée localement dans `data/bronze/questions_raw.csv`, avec son fichier de reprise ignoré par Git. Les contrôles d’exploration ont été rejoués le 24 novembre.
- Les dossiers `data/silver/`, `data/gold/`, `dbt/` et `app/` sont prêts à accueillir les étapes suivantes. Le [README](../README.md) sert de point d’entrée et la [référence technique](ARCHITECTURE.md) consigne les choix validés.

## Contrôles Bronze du 23 novembre (collecte complète)

| Contrôle | Résultat |
| --- | --- |
| Volume | 5 299 questions, 6 colonnes et 24 catégories |
| Types | 4 510 QCM et 789 questions vrai/faux |
| Difficultés | 1 770 faciles, 2 424 intermédiaires et 1 105 difficiles |
| Valeurs manquantes | 0 |
| Lignes mal formées | 0, les six champs sont présents sur chaque ligne |
| Concordance avec l’état local de collecte | 5 299 lignes et 24 catégories dans les deux fichiers |
| Doublons stricts sur les six colonnes | 0 |
| Libellés de question répétés | 4 libellés, soit 8 lignes au total |

L’empreinte SHA-256 de `data/bronze/questions_raw.csv` est `cd2b093512002f0e58c0c9f04fb1bc84ee7168d86c7b6e1f8e4d4a1f60e73d99`.

## Diagnostic avant Silver

Une simulation en mémoire du décodage HTML, de la normalisation Unicode NFC et du retrait des espaces en bord de champ conserve 5 299 lignes distinctes. Les 4 510 QCM ont chacun quatre choix distincts. Les 789 questions vrai/faux ont chacune les choix `True` et `False`. Aucun champ vide n’a été relevé après ces transformations. Le pilote de 50 questions passe les mêmes contrôles et ne contient aucun libellé répété.

La comparaison des libellés nettoyés sans tenir compte de la casse retrouve les quatre paires détectées par `exploration.py` sur les libellés bruts.

## Conversion Parquet avant dédoublonnage

`preparer_silver.py convertir` écrit `data/silver/questions_avant_dedoublonnage.parquet`. La relecture avec DuckDB a confirmé l’égalité des 5 299 lignes et des six colonnes avec le CSV, dont les huit lignes qui partagent quatre libellés.

## Dédoublonnage Silver

`preparer_silver.py dedoublonner` lit le Parquet de conversion et conserve une ligne par paire pour donner le même poids à chaque libellé dans le benchmark. Les numéros de ligne Bronze incluent l’en-tête du CSV. Le script reconnaît les variantes par leurs valeurs.

| Question | Ligne Bronze retenue | Ligne Bronze écartée de Silver | Motif |
| --- | ---: | ---: | --- |
| Apparition du type Fée dans Pokémon | 1782 | 362 | `Entertainment: Video Games` est la catégorie la plus précise. |
| Nombre de côtés d’un heptagone | 3425 | 3432 | Les mauvaises réponses `8`, `6` et `5` sont plus proches de `7`. |
| Début de la Révolution française | 4426 | 4423 | `1789` correspond à la précision du libellé. Les quatre choix sont des années. |
| Auteur de la Joconde | 4589 | 4584 | Michel-Ange est un choix plus plausible que Claude Monet pour un tableau de la Renaissance. |

Le fichier `data/silver/questions_clean.parquet` contient 5 295 questions et les six colonnes Bronze. Les champs des lignes retenues conservent leurs valeurs brutes, y compris les espaces et les entités HTML.

Un essai dans un répertoire temporaire a reproduit les 5 295 lignes à partir du seul Parquet de conversion. Un second essai a vérifié le signalement d’une paire sans arbitrage validé.

## Étapes 2 à 5 de Silver validées

`.venv/bin/python preparer_silver.py normaliser` lit `data/silver/questions_clean.parquet` et écrit `data/silver/questions_normalisees.parquet`. Les effectifs portent sur le Parquet relu. Chaque réponse incorrecte compte comme une valeur textuelle.

| Traitement | Lignes concernées | Valeurs concernées |
| --- | ---: | ---: |
| Décodage des entités HTML | 2 645 | 3 375 |
| Décodage URL, aucune séquence `%HH` détectée | 0 | 0 |
| Conversion du JSON en liste Parquet | 5 295 | 5 295 listes contenant 14 307 réponses |
| Mise en NFC après décodage HTML | 0 | 0 |
| Retrait des espaces périphériques | 265 | 309 |
| Réduction des espaces ordinaires répétés à l’intérieur | 29 | 32 |

Les deux opérations sur les espaces touchent ensemble 293 lignes. Au total, 2 781 lignes contiennent au moins une valeur textuelle modifiée. Les espaces insécables isolés issus de `&nbsp;` restent présents dans deux libellés. Les 34 valeurs contenant un signe `+` le conservent.

La comparaison des deux Parquet ligne par ligne dans DuckDB confirme le même ordre, les mêmes six colonnes et 5 295 questions, dont 4 506 QCM et 789 vrai/faux. Les 24 catégories d’origine correspondent chacune à un seul libellé de sortie. Quatre libellés contenaient `&amp;`, décodé en `&` sur 647 lignes. Les trois effectifs de difficulté et l’ordre des réponses incorrectes sont conservés. Le contrôle a aussi confirmé la présence de quatre choix distincts pour chaque QCM et des choix `True` et `False` pour chaque vrai/faux, ainsi que l’absence de texte vide ou hors NFC. Un contrôle ciblé sur des données synthétiques a vérifié la composition NFC, le décodage de guillemets dans une liste déjà parsée et le signalement d’un JSON mal formé ou d’un objet JSON à la place d’une liste.

Les empreintes SHA-256 des fichiers Bronze et Silver préexistants concordent avant et après l’exécution. Le jalon de dédoublonnage `questions_clean.parquet` conserve l’empreinte `619d09d8a553bdc33625954fac1912bac29e0fae454cc7adc049f3a098abe8af`. Le nouveau jalon validé `questions_normalisees.parquet` a l’empreinte `5434aa0bea5441f11e66882ec666d86479b34399bbfe9b03e8ddb68253238ee7`.

## Inventaire des fichiers Silver

Les dimensions ont été relues dans les métadonnées des fichiers existants. La colonne « Génération » indique les commandes historiques.

| Fichier dans `data/silver/` | Lignes × colonnes | Utilité et transformations appliquées | Génération | Conservation |
| --- | ---: | --- | --- | --- |
| `questions_avant_dedoublonnage.parquet` | 5 299 × 6 | Entrée du dédoublonnage. Conversion du CSV Bronze en Parquet. Toutes les lignes et les six champs texte sont conservés, y compris le JSON des mauvaises réponses sous forme de texte. | `preparer_silver.py convertir` | Intermédiaire requis pour rejouer le dédoublonnage tel qu’il est implémenté. Régénérable à partir de Bronze. |
| `questions_clean.parquet` | 5 295 × 6 | Résultat du dédoublonnage validé. Une ligne a été écartée dans chacune des quatre paires arbitrées. Les six champs des lignes retenues conservent leurs valeurs brutes. | `preparer_silver.py dedoublonner` | À conserver comme référence du dédoublonnage validé et source de la normalisation. |
| `questions_normalisees.parquet` | 5 295 × 6 | Résultat validé des étapes 2 à 5. `incorrect_answers` est une liste de textes. | `preparer_silver.py normaliser` | À conserver comme jalon Silver validé et base du lot 2. |
| `questions_benchmark.parquet` | 5 295 × 9 | Essai de préparation sur tout le Silver dédoublonné. Décodage HTML, Unicode NFC, retrait des espaces périphériques, conversion des mauvaises réponses JSON en liste. Ajout de `question_id` (SHA-256 du contenu normalisé), `choices` (ordre déterministe avec la seed 42) et `correct_choice` (lettre attendue). | `preparer_silver.py pilote` | Facultatif comme trace de l’essai. Préparation non validée. |
| `pilot_question_ids.parquet` | 530 × 3 | Manifeste issu des données d’essai en mémoire, dans la même exécution que la création de `questions_benchmark.parquet`. Échantillonnage stratifié par catégorie, difficulté et type avec la seed 42. Seuls le rang, l’identifiant et la seed sont enregistrés. | `preparer_silver.py pilote` | Trace provisoire, invalide pour le benchmark final. |

## Constats sur l’essai provisoire

L’essai a vérifié l’unicité des identifiants et des libellés normalisés, le nombre et l’unicité des choix, ainsi que la correspondance de la lettre attendue avec la bonne réponse. Les empreintes des fichiers Bronze et des deux Parquet Silver d’entrée concordaient avant et après l’essai. Ces vérifications techniques portent sur cet essai.

Le manifeste provisoire compte 530 identifiants distincts, soit 10,01 % du dataset de l’essai. La répartition conjointe couvre 109 des 141 strates. L’effectif de chaque strate s’écarte de son quota théorique de moins d’une question.

| Dimension | Population Silver | Pilote | Écart maximal de proportion |
| --- | ---: | ---: | ---: |
| Catégorie | 24 catégories | 24 catégories | 0,38 point |
| Difficulté | 1 767 faciles, 2 424 intermédiaires, 1 104 difficiles | 179 faciles, 242 intermédiaires, 109 difficiles | 0,40 point |
| Type | 4 506 QCM, 789 vrai/faux | 454 QCM, 76 vrai/faux | 0,56 point |

Deux reproductions dans un répertoire temporaire avec les lignes du Silver source inversées ont produit les mêmes données préparées et les mêmes identifiants dans le même ordre. La chaîne complète rejouée sur une copie du CSV Bronze a donné le même résultat. Le SHA-256 des identifiants ordonnés, séparés et terminés par un saut de ligne LF, est `1512db3e5929a74a7fe7cce4374789e29906fc23680e9eebec4e300574878122`.

## Prochain jalon

Le lot 2 partira du jalon validé `questions_normalisees.parquet` à la prochaine instruction de l’utilisatrice. L’enrichissement des champs et la définition des identifiants restent à traiter. L’échantillon de 10 % sera constitué à partir du fichier Silver définitif après validation. La commande `pilote` présentée dans le README combine actuellement préparation et échantillonnage. Son exécution est suspendue.

Le pilote Gemma 4 E2B via LM Studio avec `P1_choices` et `P2_expert` attendra ce nouvel échantillon. Les résultats et les mesures restent à produire. [Protocole du benchmark](ARCHITECTURE.md#benchmark)

Attendre la validation de l’utilisatrice avant le traitement complet ou le choix d’un deuxième modèle. Les modèles dbt, les indicateurs Gold et l’application Streamlit restent à réaliser.
