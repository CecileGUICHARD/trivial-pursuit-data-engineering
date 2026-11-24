# État d’avancement

Mis à jour le 24 novembre 2026. Le benchmark complet de Gemma 4 E2B est validé et le lot 4 est clos. Il couvre les 5 290 questions du Silver révisé par prompt et inclut les 1 060 inférences du pilote.

## Travail réalisé

- Debian sous WSL, VS Code et `.venv` opérationnels. Le dépôt GitHub a été initialisé avec le commit `cdb0286` (« Initialisation du projet et extraction Bronze »).
- Le pilote du 23 novembre a collecté 50 questions sur 15 catégories, dont 43 QCM et 7 questions vrai/faux. Il compte 15 questions faciles, 19 intermédiaires et 16 difficiles. Les six champs sont renseignés et les libellés sont uniques. Le CSV pilote est conservé localement dans `data/bronze/questions_test_50.csv`. Il sert à vérifier le fonctionnement de la collecte.
- La collecte complète du 23 novembre est disponible dans `data/bronze/questions_raw.csv`. Son fichier de reprise reste ignoré par Git. Les contrôles d’exploration ont été rejoués le 24 novembre.
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
| `candidat_final/questions_clean.parquet` | 5 295 × 10 | Six champs source, huit corrections validées et quatre champs d’enrichissement. | Première finalisation du lot 2. | Corpus historique du tirage Gemma. |
| `candidat_final_5290/questions_clean.parquet` | 5 290 × 10 | Corpus enrichi après les cinq arbitrages de doublons. | `preparer_silver.py finaliser` | Candidat reproductible. |
| `questions_clean.parquet` | 5 290 × 10 | Corpus Silver courant pour le benchmark. | Publication du candidat après accord explicite. | Livrable Silver révisé. |

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

Le 24 novembre 2026, l’utilisatrice a donné sa validation définitive au candidat de 5 295 lignes × 10 colonnes et accepté l’écart résiduel des effectifs du rapport qualité comme non bloquant. Le fichier validé a été publié par copie et remplacement atomique. Le rapport a été repris tel quel avec les décisions, les avant/après et les limites du benchmark. Aucun contrôle supplémentaire n’a été exécuté à la publication. [Candidat historique](../data/silver/candidat_final/questions_clean.parquet) · [Rapport historique](../data/silver/candidat_final/rapport_qualite_silver.csv)

La vérification en lecture seule du 24 novembre confirme que le Parquet et le rapport publiés sont identiques aux fichiers du candidat. Le SHA-256 du Parquet publié correspond à l’empreinte du candidat ci-dessus. La relecture a vérifié les huit corrections, les 5 295 identifiants uniques, leur recalcul, la cohérence des choix et des réponses attendues, ainsi que le rattachement du rapport aux identifiants du Silver définitif.

La première publication GitHub a partagé le CSV Bronze, les quatre jalons Parquet Silver et les trois CSV de qualité. Les tailles et les schémas ont été vérifiés en lecture seule. La conversion, le dédoublonnage et la normalisation concordent avec les transformations documentées. Le diagnostic et son classement concordent avec les entrées reprises dans le rapport historique. La recherche de secrets et de données confidentielles dans les textes et les métadonnées Parquet n’a rien relevé.

## Révision du Silver après les cinq arbitrages

Les dix couples `question_id` et libellé exact du CSV arbitré concordent avec le corpus initial. Les cinq décisions `EXCLURE` concernent Nephelococcygia, le chêne *Quercus robur*, la planète la plus chaude, le plus grand pays et *The Starry Night*. Le contrôle neutralisant ponctuation, guillemets, casse et espaces a signalé cinq groupes avant application et zéro après. Les cinq exclusions laissent 4 501 QCM et 789 vrai/faux sur 24 catégories. La comparaison ligne à ligne confirme l’égalité des dix champs et de l’ordre relatif pour les 5 290 questions conservées.

`preparer_silver.py finaliser` a reproduit le candidat et le rapport à la seconde exécution. Le rapport ajoute les cinq décisions `GARDER` et les cinq décisions `EXCLURE` aux 1 035 entrées historiques. Les nouveaux rangs d’audit renvoient au corpus enrichi de 5 295 questions avant exclusion. Le SHA-256 du corpus révisé est `af2e683573b68effb0832fff695e3acfeb138e3a67449ebd306814a00f67a92e`. [Silver révisé](../data/silver/questions_clean.parquet) · [Rapport qualité révisé](../data/silver/rapport_qualite_silver.csv)

## Pilote Gemma 4 E2B sur le Silver définitif

L’utilisatrice a approuvé le protocole du lot 3 et le tirage stratifié avec la seed 42. `pilote_gemma.py manifeste` a sélectionné 530 identifiants du Silver initial, soit 10,01 % des 5 295 questions, dans 109 des 141 strates et les 24 catégories. Le tirage a donné les mêmes identifiants dans le même ordre après inversion des lignes source. [Manifeste du pilote](../data/silver/pilot_lot2/pilot_question_ids.parquet) · [Métadonnées et empreintes](../data/silver/pilot_lot2/manifest_metadata.json)

Le manifeste compte 454 QCM et 76 vrai/faux, dont 179 faciles, 242 intermédiaires et 109 difficiles. Son SHA-256 est `f130cda8a5ca4c21c2a40016d3154d3f37bcb9de9c94446814afc460687305e5`.

Aucune des cinq exclusions ne figure au pilote. Le manifeste a conservé son empreinte initiale. Les métadonnées distinguent le corpus de tirage et le corpus actif, et l’empreinte de reprise a été révisée dans le journal. Les 1 060 enregistrements préservent leurs configurations historiques. Un essai de reprise sur une copie du journal a confirmé que le contrôle des empreintes et la relecture aboutissent hors réseau.

Le script utilise Gemma 4 E2B Q4_K_M dans LM Studio `0.4.28+2`, avec le moteur Vulkan llama.cpp `2.80.1`. Depuis WSL, le client `curl.exe` accède au serveur Windows sur la boucle locale. Une instance dédiée à 4 096 tokens sert les deux blocs. Des essais synthétiques ont vérifié le scoring strict, le traitement d’un délai expiré et d’une réponse illisible, la reprise sans duplication après interruption et le rejet d’une configuration différente. [Script d’exécution](../pilote_gemma.py) · [Protocole du benchmark](ARCHITECTURE.md#benchmark)

### Résultats du pilote

Les 1 060 tentatives ont été reprises du journal local. Les deux tables Bronze de 530 lignes conservent les réponses brutes, temps, statuts, identifiants et configurations d’origine. Les deux tables Silver de 530 lignes ont été régénérées à partir du Bronze et des réponses attendues. La comparaison ligne par ligne avec le journal confirme les mêmes valeurs, les 1 060 UUID uniques, les scores d’origine et l’ordre du manifeste. [Bronze P1](../data/bronze/gemma_p1_choices.parquet) · [Bronze P2](../data/bronze/gemma_p2_expert.parquet) · [Silver P1](../data/silver/gemma_p1_choices.parquet) · [Silver P2](../data/silver/gemma_p2_expert.parquet)

Le nouveau flux a été testé hors ligne avec un journal vierge, un export vide, un délai d’attente expiré, une réponse hors format et une reprise après collecte. Le journal local d’origine est resté identique. La reconstruction et la structuration du lot 3 ont utilisé les mesures existantes.

| Mesure | `P1_choices` | `P2_expert` |
| --- | ---: | ---: |
| Réponses correctes sur 530 | 301 (56,79 %) | 304 (57,36 %) |
| QCM corrects sur 454 | 252 | 257 |
| Vrai/faux corrects sur 76 | 49 | 47 |
| Réponses conformes | 530 (100 %) | 530 (100 %) |
| Erreurs techniques | 0 | 0 |
| Latence moyenne | 0,594 s | 0,618 s |
| Latence médiane | 0,559 s | 0,584 s |
| Durée active mesurée | 378,81 s | 392,25 s |
| Projection sur les 5 290 questions | 1 h 03 min 01 s | 1 h 05 min 15 s |
| Temps restant en réutilisant le pilote | 56 min 42 s | 58 min 43 s |

Sur les 530 paires, 11 questions sont correctes uniquement avec `P2_expert` et huit uniquement avec `P1_choices`. L’écart d’exactitude observé est de 0,57 point en faveur de `P2_expert`. La durée active cumulée est de 12 min 51 s. En conditions comparables, l’estimation pour les deux prompts est de 2 h 08 min 16 s depuis zéro, ou 1 h 55 min 25 s pour les 4 760 questions restantes par prompt.

## Benchmark Gemma du lot 4

L’utilisatrice a autorisé le traitement des questions restantes. Les deux instances à 8 192 tokens ont été déchargées. L’instance `gemma-pilote-lot3` a été rechargée avec Gemma 4 E2B Q4_K_M, un contexte de 4 096 tokens et le moteur Vulkan `2.80.1`. La configuration exposée par LM Studio et les réglages d’inférence correspondent au journal du pilote.

Le journal du lot 4 a repris les 1 060 tentatives du pilote et ajouté 4 760 tentatives par prompt, `P1_choices` puis `P2_expert`. Le contrôle final a vérifié l’ensemble exact des 5 290 `question_id` du corpus dans les quatre Parquet, leur ordre commun et les 10 580 identifiants d’inférence distincts. Les champs communs Bronze–Silver correspondent ligne à ligne et les résultats structurés concordent avec le scoring recalculé. [Bronze P1](../data/bronze/benchmark_lot4/gemma_p1_choices.parquet) · [Bronze P2](../data/bronze/benchmark_lot4/gemma_p2_expert.parquet) · [Silver P1](../data/silver/benchmark_lot4/gemma_p1_choices.parquet) · [Silver P2](../data/silver/benchmark_lot4/gemma_p2_expert.parquet)

| Mesure | `P1_choices` | `P2_expert` |
| --- | ---: | ---: |
| Réponses reçues | 5 290 | 5 290 |
| Réponses correctes | 2 863 (54,12 %) | 2 852 (53,91 %) |
| QCM corrects sur 4 501 | 2 431 | 2 423 |
| Vrai/faux corrects sur 789 | 432 | 429 |
| Réponses conformes | 5 290 (100 %) | 5 290 (100 %) |
| Erreurs techniques | 0 | 0 |
| Latence moyenne | 0,463 s | 0,466 s |
| Latence médiane | 0,448 s | 0,445 s |
| Durée active avec le pilote | 2 988,84 s | 3 094,93 s |

Sur les 5 290 paires, 89 questions sont correctes uniquement avec `P1_choices` et 78 uniquement avec `P2_expert`. L’écart observé est de 0,21 point en faveur de `P1_choices`. La durée active cumulée est de 1 h 41 min 24 s, dont 12 min 51 s mesurées au pilote.

## Prochain jalon

Attendre la validation de l’utilisatrice avant le choix d’un deuxième modèle. Les modèles dbt, les indicateurs Gold et l’application Streamlit restent à réaliser.
