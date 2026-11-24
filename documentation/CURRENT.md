# État d’avancement

Mis à jour le 24 novembre 2026. Le lot 2 est clos. L’utilisatrice a validé définitivement le Silver de 5 295 lignes × 10 colonnes, publié dans `data/silver/questions_clean.parquet`. Il part du jalon `data/silver/questions_normalisees.parquet` et applique les huit corrections autorisées. Le pilote généré au cours de l’essai reste provisoire.

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

Le jalon archivé dans `data/silver/questions_dedoublonnees.parquet` contient 5 295 questions et les six colonnes Bronze. Les champs des lignes retenues conservent leurs valeurs brutes, y compris les espaces et les entités HTML. Le jalon occupait `data/silver/questions_clean.parquet` avant la publication du lot 2.

Un essai dans un répertoire temporaire a reproduit les 5 295 lignes à partir du seul Parquet de conversion. Un second essai a vérifié le signalement d’une paire sans arbitrage validé.

## Étapes 2 à 5 de Silver validées

`.venv/bin/python preparer_silver.py normaliser` lit le jalon dédoublonné, désormais nommé `data/silver/questions_dedoublonnees.parquet`, et écrit `data/silver/questions_normalisees.parquet`. Les effectifs portent sur le Parquet relu lors de la validation de la normalisation. Chaque réponse incorrecte compte comme une valeur textuelle.

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

Lors de la normalisation, les empreintes SHA-256 des fichiers Bronze et Silver préexistants concordaient avant et après l’exécution. L’empreinte du jalon dédoublonné avant son archivage était `619d09d8a553bdc33625954fac1912bac29e0fae454cc7adc049f3a098abe8af`. Celle du jalon normalisé validé était `5434aa0bea5441f11e66882ec666d86479b34399bbfe9b03e8ddb68253238ee7`.

## Inventaire des fichiers Silver

Les dimensions ont été relues dans les métadonnées des fichiers existants. La colonne « Génération » indique les commandes historiques.

| Fichier dans `data/silver/` | Lignes × colonnes | Utilité et transformations appliquées | Génération | Conservation |
| --- | ---: | --- | --- | --- |
| `questions_avant_dedoublonnage.parquet` | 5 299 × 6 | Entrée du dédoublonnage. Conversion du CSV Bronze en Parquet. Toutes les lignes et les six champs texte sont conservés, y compris le JSON des mauvaises réponses sous forme de texte. | `preparer_silver.py convertir` | Intermédiaire requis pour rejouer le dédoublonnage tel qu’il est implémenté. Régénérable à partir de Bronze. |
| `questions_dedoublonnees.parquet` | 5 295 × 6 | Résultat du dédoublonnage validé. Les champs des lignes retenues après les quatre arbitrages conservent leurs valeurs brutes. | `preparer_silver.py dedoublonner` | Jalon auparavant nommé `questions_clean.parquet`, archivé lors de la publication. |
| `questions_normalisees.parquet` | 5 295 × 6 | Résultat validé des étapes 2 à 5. `incorrect_answers` est une liste de textes. | `preparer_silver.py normaliser` | À conserver comme jalon Silver validé et base du lot 2. |
| `questions_benchmark.parquet` | 5 295 × 9 | Essai de préparation sur tout le Silver dédoublonné. Décodage HTML, Unicode NFC, retrait des espaces périphériques, conversion des mauvaises réponses JSON en liste. Ajout de `question_id` (SHA-256 du contenu normalisé), `choices` (ordre déterministe avec la seed 42) et `correct_choice` (lettre attendue). | `preparer_silver.py pilote` | Facultatif comme trace de l’essai. Préparation non validée. |
| `pilot_question_ids.parquet` | 530 × 3 | Manifeste issu des données d’essai en mémoire, dans la même exécution que la création de `questions_benchmark.parquet`. Échantillonnage stratifié par catégorie, difficulté et type avec la seed 42. Seuls le rang, l’identifiant et la seed sont enregistrés. | `preparer_silver.py pilote` | Trace provisoire, invalide pour le benchmark final. |
| `candidat_final/questions_clean.parquet` | 5 295 × 10 | Six champs source, huit corrections validées et quatre champs d’enrichissement. | `preparer_silver.py finaliser` | Copie du candidat validé. |
| `questions_clean.parquet` | 5 295 × 10 | Corpus Silver définitif pour le benchmark. | Publication du candidat après accord explicite. | Livrable du lot 2. |

## Constats sur l’essai provisoire

L’essai a vérifié l’unicité des identifiants et des libellés normalisés, le nombre et l’unicité des choix, ainsi que la correspondance de la lettre attendue avec la bonne réponse. Les empreintes des fichiers Bronze et des deux Parquet Silver d’entrée concordaient avant et après l’essai. Ces vérifications techniques portent sur cet essai.

Le manifeste provisoire compte 530 identifiants distincts, soit 10,01 % du dataset de l’essai. La répartition conjointe couvre 109 des 141 strates. L’effectif de chaque strate s’écarte de son quota théorique de moins d’une question.

| Dimension | Population Silver | Pilote | Écart maximal de proportion |
| --- | ---: | ---: | ---: |
| Catégorie | 24 catégories | 24 catégories | 0,38 point |
| Difficulté | 1 767 faciles, 2 424 intermédiaires, 1 104 difficiles | 179 faciles, 242 intermédiaires, 109 difficiles | 0,40 point |
| Type | 4 506 QCM, 789 vrai/faux | 454 QCM, 76 vrai/faux | 0,56 point |

Deux reproductions dans un répertoire temporaire avec les lignes du Silver source inversées ont produit les mêmes données préparées et les mêmes identifiants dans le même ordre. La chaîne complète rejouée sur une copie du CSV Bronze a donné le même résultat. Le SHA-256 des identifiants ordonnés, séparés et terminés par un saut de ligne LF, est `1512db3e5929a74a7fe7cce4374789e29906fc23680e9eebec4e300574878122`.

## Diagnostic linguistique du lot 2

Le 24 novembre 2026, le contrôle a porté sur les 24 897 textes du jalon Silver validé, soit 5 295 questions, 5 295 bonnes réponses et 14 307 réponses incorrectes. La relecture intégrale a été complétée par Hunspell avec des dictionnaires anglais américain et britannique, et par LanguageTool 6.6. Le [rapport de validation](../data/silver/diagnostic_anglais_lot2.csv) contient 1 019 propositions pour 932 lignes et 11 cas à éclaircir. Il indique le rang Silver à partir de 1 et la ligne Bronze en comptant l’en-tête du CSV. Chaque proposition présente le champ, le texte d’origine, le texte proposé et la justification.

Le contrôle de référence a trouvé zéro doublon strict sur les six colonnes et zéro libellé de question répété, avec ou sans distinction de casse. Le diagnostic a été réalisé en lecture seule sur Bronze et Silver.

Le [classement initial](../data/silver/classement_diagnostic_anglais_lot2.csv) conserve les identifiants et les avant/après proposés. Il compte 570 propositions dans les trois groupes, 403 propositions à examiner individuellement, 46 retouches stylistiques ou factuelles et 11 cas à éclaircir en plus des 1 019 propositions. L’arbitrage final a été limité aux anomalies prioritaires.

## Candidat Silver après arbitrage

L’accord couvre six libellés (`S00646-q`, `S01104-q`, `S02234-q`, `S02686-q`, `S03037-q`, `S04170-q`) et deux bonnes réponses (`S03139-c`, `H20` → `H2O`, et `S03184-c`, `Cascading Style Sheet` → `Cascading Style Sheets`). L’ordre des lignes et des distracteurs dans les six champs source est conservé. Aucune question n’a été exclue.

`.venv/bin/python -B preparer_silver.py finaliser` a écrit et relu le [Parquet candidat](../data/silver/candidat_final/questions_clean.parquet) ainsi que le [rapport qualité](../data/silver/candidat_final/rapport_qualite_silver.csv). Le rapport contient les 1 030 entrées du classement initial et cinq propositions de l’arbitrage final sur des champs associés. Les décisions se répartissent en 8 appliquées, 1 018 non retenues et 9 laissées en l’état. Les avant/après sont rattachés au rang Silver initial, à la ligne Bronze et au `question_id` du candidat.

| Contrôle exécuté | Résultat |
| --- | --- |
| Volume et conservation des catégories | 5 295 lignes, 4 506 QCM, 789 vrai/faux et 24 catégories. Types, difficultés et catégories identiques ligne par ligne. |
| Schéma et complétude | 10 colonnes. Valeurs textuelles et listes typées, aucune valeur nulle ou vide. `category_id` est entier. |
| Comparaison source et candidat dans DuckDB | 8 champs modifiés aux rangs approuvés. Les distracteurs et toutes les autres valeurs des six champs source concordent. |
| Doublons et identifiants | 0 doublon strict et 0 libellé répété avec ou sans distinction de casse, à la source et après relecture. 5 295 identifiants distincts. |
| Choix et scoring | 4 ou 2 choix distincts par question, bonne réponse présente exactement une fois. `expected_answer` correspond à sa position en QCM ou à la chaîne `True`/`False`. |
| Reproductibilité | Identifiants, choix et réponses attendues identiques après inversion des lignes et des distracteurs. Une seconde finalisation a reproduit le Parquet relu et le rapport. |
| Intégrité et relecture | Schéma et contenu relus conformes. Empreintes SHA-256 des fichiers Bronze et Silver préexistants concordantes. |
| Essais de rejet en mémoire | Le contrôle intercepte un avant différent du rapport, des choix dupliqués, une réponse attendue incohérente, une correction hors arbitrage et un doublon strict. |

Exemples du Parquet relu. Au rang 3139, `H2O` est le premier choix et `expected_answer` vaut `A`. Au rang 3184, `Cascading Style Sheets` est le quatrième choix et `expected_answer` vaut `D`. Au rang 4170, les choix sont `False`, puis `True`, et la réponse attendue est la chaîne `True`.

La colonne `limite_benchmark` du rapport documente 22 rangs signalés. Le corpus conserve notamment deux traductions quasi équivalentes pour `Wubba Lubba Dub Dub`, une question d’aéroport dont l’année et la métrique restent implicites, des vrai/faux dont l’interprétation dépend d’une hypothèse et des superlatifs sans critère vérifiable. Le scoring sur ces cas reste sensible à la formulation ou à la réponse de référence. Les protections prévues pour `Vulpes Vulpie` et `Cartillary Action` ont conservé les choix et la valeur de vérité d’origine.

L’empreinte SHA-256 mesurée avant la publication était `0274c8a547a78b4a6673dca152144988403d9a1cd1b6425ebba33d1e349da736`.

## Publication du Silver définitif

Le 24 novembre 2026, l’utilisatrice a donné sa validation définitive au candidat de 5 295 lignes × 10 colonnes et accepté l’écart résiduel des effectifs du rapport qualité comme non bloquant. Le fichier validé a été publié par copie et remplacement atomique. Le rapport a été repris tel quel avec les décisions, les avant/après et les limites du benchmark. Aucun contrôle supplémentaire n’a été exécuté à la publication. [Silver définitif](../data/silver/questions_clean.parquet), [rapport qualité publié](../data/silver/rapport_qualite_silver.csv), [jalon dédoublonné archivé](../data/silver/questions_dedoublonnees.parquet)

## Prochain jalon

L’échantillon de 10 % sera constitué à partir du Silver définitif lors de la prochaine étape. La commande historique `pilote` combine préparation et échantillonnage sur le jalon dédoublonné. Elle reste suspendue pour le benchmark final.

Le pilote Gemma 4 E2B via LM Studio avec `P1_choices` et `P2_expert` attendra ce nouvel échantillon. Les résultats et les mesures restent à produire. [Protocole du benchmark](ARCHITECTURE.md#benchmark)

Attendre la validation de l’utilisatrice avant le traitement complet ou le choix d’un deuxième modèle. Les modèles dbt, les indicateurs Gold et l’application Streamlit restent à réaliser.
