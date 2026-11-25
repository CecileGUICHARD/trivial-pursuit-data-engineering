# État d’avancement

Mis à jour le 25 novembre 2026. Le lot 4 est définitivement clos. L’utilisatrice a validé les benchmarks Gemma 4 E2B et Ministral 3 3B Instruct ainsi que leur comparaison sur les mêmes 5 290 questions pour `P1_choices`, `P2_expert` et `P3_expert_advanced`.

L’utilisatrice a validé l’alignement sur le schéma D42. Les sept Parquet constituent Silver et l’OBT est matérialisée dans `dbt intermediate`. Les sept marts du lot 8 sont publiés au commit `6d17118`. L’utilisatrice a validé le complément méthodologique du lot 8 bis. [Résultats du lot 8 bis](#lot-8-bis--complément-méthodologique-gold)

Les développements techniques sont clos. L’utilisatrice a validé le dashboard Streamlit et ses finitions du lot 9 bis, ainsi que l’analyse exploratoire par familles OpenTDB. [Refonte du lot 9 bis](#lot-9-bis--refonte-ergonomique-du-dashboard) · [Analyse par familles](#analyse-exploratoire-par-familles-opentdb)

## Travail réalisé

- Debian sous WSL, VS Code et `.venv` opérationnels. Le dépôt GitHub a été initialisé avec le commit `cdb0286` (« Initialisation du projet et extraction Bronze »).
- Le pilote du 23 novembre a collecté 50 questions sur 15 catégories, dont 43 QCM et 7 questions vrai/faux. Il compte 15 questions faciles, 19 intermédiaires et 16 difficiles. Les six champs sont renseignés et les libellés sont uniques. Le CSV pilote est conservé localement dans `data/bronze/questions_test_50.csv`. Il sert à vérifier le fonctionnement de la collecte.
- La collecte complète du 23 novembre est disponible dans `data/bronze/questions_raw.csv`. Son fichier de reprise reste ignoré par Git. Les contrôles d’exploration ont été rejoués le 24 novembre.
- Les dossiers `data/silver/`, `dbt/` et `app/` structurent les données préparées, les transformations et la restitution prévue. [README](../README.md) · [Référence technique](ARCHITECTURE.md)

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

L’audit en lecture seule du script et des journaux LM Studio confirme l’indépendance conversationnelle des 10 580 requêtes mesurées. Les transitions entre prompts n’incluent aucune commande de déchargement ni de réinitialisation du cache. [Garantie méthodologique](ARCHITECTURE.md#indépendance-conversationnelle)

## Pilote de P3_expert_advanced

Le bloc P3 a utilisé Gemma 4 E2B Q4_K_M, LM Studio `0.4.28+2` et le moteur Vulkan `2.80.1`. Il a repris les 530 identifiants dans l’ordre du manifeste, avec les réglages d’inférence et le scoring strict du pilote historique. L’audit des requêtes LM Studio confirme une requête indépendante par question et un échauffement synthétique. Les empreintes des Parquet et des journaux historiques P1 et P2 concordent avant et après l’exécution. [Protocole](ARCHITECTURE.md#benchmark) · [Bronze P3](../data/bronze/gemma_p3_expert_advanced.parquet) · [Silver P3](../data/silver/gemma_p3_expert_advanced.parquet)

| Mesure | `P1_choices` | `P2_expert` | `P3_expert_advanced` |
| --- | ---: | ---: | ---: |
| Réponses correctes sur 530 | 301 (56,79 %) | 304 (57,36 %) | 291 (54,91 %) |
| QCM corrects sur 454 | 252 | 257 | 246 |
| Vrai/faux corrects sur 76 | 49 | 47 | 45 |
| Réponses conformes sur 530 | 530 (100 %) | 530 (100 %) | 524 (98,87 %) |
| Erreurs techniques | 0 | 0 | 0 |
| Latence moyenne | 0,594 s | 0,618 s | 0,547 s |
| Latence médiane | 0,559 s | 0,584 s | 0,508 s |
| Durée active | 378,81 s | 392,25 s | 342,41 s |

Sur les mêmes 530 questions, P3 a obtenu 13 bonnes réponses de moins que P2, soit 2,45 points d’exactitude de moins. P2 est seul correct sur 34 questions et P3 sur 21. Les six réponses P3 hors format concernent des QCM, dont un avec une réponse brute vide. Les six comptent comme incorrectes. La commande `pilote_gemma.py bilan-p3` reproduit ces métriques depuis les journaux du pilote.

La projection pour les 4 760 questions restantes est de **51 min 15 s**, sur la base de `342,41 × 4 760 / 530` en conditions comparables. Elle réutilise les 530 mesures existantes et exclut l’échauffement.

## Comparaison complète des trois prompts

Après validation du pilote P3, `benchmark_gemma.py executer --p3` a repris ses 530 mesures et envoyé 4 760 nouvelles requêtes à la même instance Gemma 4 E2B Q4_K_M. Le contrôle de reprise a confirmé l’empreinte du prompt, les paramètres d’inférence et le moteur Vulkan `2.80.1`. Le complément a pris **49 min 59 s** de temps actif, hors échauffement. [Bronze P3 complet](../data/bronze/benchmark_lot4/gemma_p3_expert_advanced.parquet) · [Silver P3 complet](../data/silver/benchmark_lot4/gemma_p3_expert_advanced.parquet)

| Mesure | `P1_choices` | `P2_expert` | `P3_expert_advanced` |
| --- | ---: | ---: | ---: |
| Réponses reçues | 5 290 | 5 290 | 5 290 |
| Réponses correctes | 2 863 (54,12 %) | 2 852 (53,91 %) | 2 753 (52,04 %) |
| QCM corrects sur 4 501 | 2 431 | 2 423 | 2 354 |
| Vrai/faux corrects sur 789 | 432 | 429 | 399 |
| Réponses conformes | 5 290 (100 %) | 5 290 (100 %) | 5 235 (98,96 %) |
| Erreurs techniques | 0 | 0 | 0 |
| Latence moyenne | 0,463 s | 0,466 s | 0,522 s |
| Latence médiane | 0,448 s | 0,445 s | 0,491 s |
| Durée active avec le pilote | 2 988,84 s | 3 094,93 s | 3 341,34 s |

P3 obtient 110 bonnes réponses de moins que P1 (2,08 points) et 99 de moins que P2 (1,87 point). Sur les paires P2–P3, P2 est seul correct sur 399 questions et P3 sur 300. Les 55 réponses P3 hors format concernent des QCM. Elles ont été conservées telles quelles et comptées comme incorrectes, dont les six du pilote.

La relecture a confirmé les mêmes 5 290 identifiants ordonnés dans chaque Parquet et 15 870 identifiants d’inférence distincts. Les 530 premières lignes des exports P3 concordent champ par champ avec les fichiers du pilote. Le scoring strict recalculé concorde avec Silver. Les empreintes des fichiers historiques de P1, P2 et du pilote P3 concordent avant et après le complément. Le journal serveur confirme l’indépendance des 5 290 requêtes P3. La commande `benchmark_gemma.py bilan --p3` reproduit le comparatif en lecture seule. [Protocole](ARCHITECTURE.md#indépendance-conversationnelle)

## Pilote Bonsai 27B arrêté et modèle abandonné

L’utilisatrice a arrêté le pilote après **41 inférences terminées sur 90**. Gemma avait été déchargé et Bonsai 27B Q1_0 a chargé en 37,02 s. L’exécution de `P1_choices` est complète. L’arrêt a interrompu la douzième requête de `P2_expert`, conservée avec le statut `interrupted`. Le bloc `P3_expert_advanced` et le benchmark complet sont restés au stade de la préparation. Après l’arrêt, l’API LM Studio a confirmé que Bonsai était déchargé et que la liste des instances chargées était vide. L’utilisatrice a validé l’abandon définitif de Bonsai pour des raisons de faisabilité matérielle. [Configuration](ARCHITECTURE.md#pilote-bonsai-27b)

| Mesure | `P1_choices` | `P2_expert` |
| --- | ---: | ---: |
| Réponses reçues | 30 | 11 |
| Réponses conformes | 30 | 11 |
| Réponses correctes | 17 | 6 |
| Erreurs techniques | 0 | 0 |
| Requêtes interrompues à l’arrêt | 0 | 1 |
| Latence moyenne | 14,81 s | 16,33 s |
| Latence médiane | 16,14 s | 15,88 s |
| Durée active | 449,76 s | 193,28 s |

La latence moyenne sur les 41 réponses est de **15,22 s** et la durée active cumulée des deux segments est de **10 min 43 s**. En appliquant cette latence moyenne aux 15 870 inférences du benchmark complet, le temps d’inférence est estimé à **67 h 05** depuis zéro, ou **66 h 55** pour les 15 829 inférences restantes après reprise des 41 mesures. Cette extrapolation exclut les échauffements et la persistance. Elle suppose des latences comparables à celles des réponses observées, y compris pour P3, dont la durée reste inconnue.

Le modèle est abandonné pour ce benchmark sur la machine actuelle en raison de la pression mémoire et du temps de traitement extrapolé. Sur 44 relevés Windows du processus `llama-server`, le maximum observé est de 5,79 Gio de mémoire GPU partagée sur l’Intel UHD et de 14,30 Gio de mémoire privée engagée par le processus. Ces compteurs se lisent séparément. La mémoire physique totale signalée par Windows est de 15,75 Gio. Un relevé pendant le pilote indiquait 444 Mio de mémoire physique disponible. [Relevés mémoire](../data/silver/pilote_bonsai/memoire.jsonl)

Les mesures et la tentative interrompue sont conservées dans le journal DuckDB et les Parquet Bonsai. L’audit du journal LM Studio retrouve 42 appels du pilote, deux échauffements et une requête synthétique de contrôle. Chacun transmet un seul message avec `store=false`. La relecture des exports vérifie l’ordre du manifeste, les champs communs entre Bronze et Silver et le scoring strict. Les empreintes SHA-256 des 41 fichiers de données Bronze et Silver présents avant le pilote concordent, y compris les fichiers Gemma. [Mesures Bronze](../data/bronze/pilote_bonsai/) · [Résultats et journal Silver](../data/silver/pilote_bonsai/)

Les résultats partiels Bonsai sont conservés localement pour la traçabilité. La future comparaison Gold des benchmarks complets exclura l’ensemble de ces mesures. [Périmètre Gold](ARCHITECTURE.md#gold-et-restitution)

## Test de faisabilité Qwen3-4B-Instruct-2507

L’utilisatrice a validé les résultats du test de faisabilité. Les 90 inférences sont conservées localement, y compris les 31 réponses hors format.

Qwen a remplacé Bonsai pour le test de faisabilité du 24 novembre 2026. Les 90 inférences ont repris les 30 questions du manifeste Bonsai, dans le même ordre, avec les trois prompts et les choix d’origine. L’instance `qwen-benchmark-lot4` a chargé le GGUF Q4_K_M en 9,95 s avec un contexte de 4 096 tokens dans LM Studio `0.4.28+2` et le moteur Vulkan `2.80.1`. Les réglages Gemma compatibles ont été repris. La variante Instruct fonctionne uniquement sans mode de réflexion, ce qui rend le champ `reasoning` inutile. [Configuration et reproduction](ARCHITECTURE.md#pilote-qwen3-4b-instruct-2507)

| Mesure | `P1_choices` | `P2_expert` | `P3_expert_advanced` |
| --- | ---: | ---: | ---: |
| Réponses reçues | 30/30 | 30/30 | 30/30 |
| Réponses correctes au scoring strict | 15 (50,0 %) | 14 (46,7 %) | 0 (0 %) |
| Réponses conformes | 30 (100 %) | 29 (96,7 %) | 0 (0 %) |
| Erreurs techniques | 0 | 0 | 0 |
| Latence HTTP moyenne | 0,893 s | 0,827 s | 3,300 s |
| Latence HTTP médiane | 0,838 s | 0,773 s | 3,209 s |
| Durée active de 30 tentatives | 30,49 s | 27,72 s | 102,40 s |
| Projection sur 5 290 tentatives | 1 h 29 min 37 s | 1 h 21 min 28 s | 5 h 00 min 57 s |

L’unique réponse P2 hors format est `D. Seiren` au rang 23. Les 30 sorties P3 contiennent du texte explicatif et atteignent chacune le plafond de 16 tokens d’après le journal LM Studio. Même lorsqu’une réponse commence par `False`, l’explication qui suit invalide le format strict. Les 31 sorties hors format sont conservées en Bronze et comptées comme incorrectes en Silver.

Les trois blocs cumulent **2 min 40,61 s** de temps actif. L’extrapolation par prompt donne **7 h 52 min 02 s** pour les 15 870 tentatives depuis zéro, ou **7 h 49 min 21 s** pour les 15 780 restantes en réutilisant les 90 mesures. Le calcul applique la durée active des 30 tentatives de chaque bloc à 5 290 ou 5 260 tentatives. Il inclut la persistance, exclut le chargement et les échauffements et suppose des conditions comparables. L’échantillon de 30 questions donne un ordre de grandeur.

Un relevé ponctuel pendant le pilote indiquait environ 256 Mio de mémoire physique disponible sur les 15,75 Gio de Windows et 3,70 Gio de mémoire privée engagée par `llama-server`. À la fin du pilote, la mémoire physique disponible mesurée est passée d’environ 610 Mio à 5,67 Gio après déchargement. LM Studio a confirmé que la liste des instances chargées était alors vide.

L’audit du journal LM Studio confirme 90 requêtes mesurées et trois échauffements, chacun avec un seul message, `store=false`, sans identifiant de réponse précédente. Les extraits d’`input` concordent avec les prompts attendus. La relecture du journal DuckDB et des six Parquet vérifie les 90 identifiants distincts, l’ordre du manifeste, les champs communs Bronze–Silver et le scoring recalculé. Les SHA-256 des 49 fichiers Bronze et Silver présents avant le pilote concordent, y compris toutes les données Gemma et Bonsai. [Mesures Bronze](../data/bronze/pilote_qwen/) · [Résultats Silver](../data/silver/pilote_qwen/) · [Journal DuckDB](../data/silver/pilote_qwen/pilot.duckdb)

## Test de faisabilité Ministral-3-3B-Instruct-2512

Le 24 novembre 2026, le test a exécuté les 90 inférences sur les mêmes 30 questions que Bonsai et Qwen, dans le même ordre et avec les trois gabarits d’origine. L’instance `ministral-benchmark-lot4` a chargé le GGUF Instruct Q4_K_M en 9,19 s avec un contexte de 4 096 tokens dans LM Studio `0.4.28+2` et le moteur Vulkan `2.80.1`. Le plafond de sortie était de 16 tokens. Le déchargement a été confirmé par l’API LM Studio. [Configuration et reproduction](ARCHITECTURE.md#pilote-ministral-3-3b-instruct-2512)

| Mesure | `P1_choices` | `P2_expert` | `P3_expert_advanced` |
| --- | ---: | ---: | ---: |
| Réponses reçues | 30/30 | 30/30 | 30/30 |
| Bonnes réponses | 12 | 12 | 9 |
| Mauvaises réponses | 18 | 18 | 21 |
| Exactitude stricte | 40,0 % | 40,0 % | 30,0 % |
| Réponses conformes | 30 (100 %) | 30 (100 %) | 22 (73,3 %) |
| Erreurs techniques | 0 | 0 | 0 |
| Latence HTTP moyenne | 0,769 s | 0,795 s | 1,425 s |
| Latence HTTP médiane | 0,749 s | 0,786 s | 0,876 s |
| Durée active | 26,18 s | 27,03 s | 46,32 s |
| Projection sur 5 290 tentatives | 1 h 16 min 56 s | 1 h 19 min 26 s | 2 h 16 min 08 s |
| Projection sur les 5 260 restantes | 1 h 16 min 29 s | 1 h 18 min 59 s | 2 h 15 min 22 s |

Les huit sorties P3 hors format concernent les QCM aux rangs 5, 6, 8, 15, 20, 24, 27 et 30. Elles ajoutent la formule `The correct answer is` et du Markdown autour de la lettre, parfois accompagnée du texte du choix. Cinq atteignent le plafond de 16 tokens et trois s’arrêtent à 9 tokens. Le scoring strict compte les huit comme incorrectes, y compris les trois qui contiennent la lettre attendue. Les trois vrai/faux sont conformes. Qwen avait produit 30 réponses hors format sur ce bloc.

Les trois blocs cumulent **1 min 39,52 s** de temps actif. La projection est de **4 h 52 min 29 s** pour les 15 870 tentatives depuis zéro, ou **4 h 50 min 50 s** pour les 15 780 restantes en réutilisant le pilote. Le calcul applique la durée active de chaque bloc de 30 tentatives au volume correspondant. Il inclut la persistance et exclut le chargement et les échauffements. Les projections supposent des conditions comparables et donnent un ordre de grandeur à partir de 30 questions par prompt.

Sur les 20 relevés Windows pris pendant le pilote, la mémoire physique disponible a atteint un minimum de 494 Mio sur 15,75 Gio. Le processus `llama-server` a atteint 3,70 Gio de mémoire privée engagée et 5,35 Gio d’ensemble de travail. Les compteurs se lisent séparément. La mémoire physique disponible était de 5,83 Gio avant chargement et de 6,61 Gio après déchargement. [Relevés mémoire](../data/silver/pilote_ministral/memoire.jsonl)

L’audit des journaux LM Studio retrouve 90 requêtes mesurées et trois échauffements avec un seul message, `store=false`, sans identifiant de réponse précédente. Les extraits d’`input` concordent avec les prompts attendus, et les réponses du serveur concordent avec le journal DuckDB. La relecture des six Parquet confirme 90 identifiants d’inférence distincts, l’ordre du manifeste, l’égalité des champs communs Bronze–Silver et le scoring recalculé. Les empreintes SHA-256 des 56 fichiers Bronze et Silver préexistants concordent. [Mesures Bronze](../data/bronze/pilote_ministral/) · [Résultats Silver](../data/silver/pilote_ministral/) · [Journal DuckDB](../data/silver/pilote_ministral/pilot.duckdb)

### Comparaison des trois tests de faisabilité

| Modèle | Prompt | Bonnes réponses | Conformité | Latence moyenne / médiane | Durée active |
| --- | --- | ---: | ---: | ---: | ---: |
| Bonsai 27B | P1 | 17/30 (56,7 %) | 30/30 (100 %) | 14,812 / 16,143 s | 449,76 s |
| Bonsai 27B | P2 | 6/11 (54,5 %) | 11/11 (100 %) | 16,330 / 15,881 s | 193,28 s |
| Bonsai 27B | P3 | — | — | — | — |
| Qwen3 4B Instruct | P1 | 15/30 (50,0 %) | 30/30 (100 %) | 0,893 / 0,838 s | 30,49 s |
| Qwen3 4B Instruct | P2 | 14/30 (46,7 %) | 29/30 (96,7 %) | 0,827 / 0,773 s | 27,72 s |
| Qwen3 4B Instruct | P3 | 0/30 (0 %) | 0/30 (0 %) | 3,300 / 3,209 s | 102,40 s |
| Ministral 3 3B Instruct | P1 | 12/30 (40,0 %) | 30/30 (100 %) | 0,769 / 0,749 s | 26,18 s |
| Ministral 3 3B Instruct | P2 | 12/30 (40,0 %) | 30/30 (100 %) | 0,795 / 0,786 s | 27,03 s |
| Ministral 3 3B Instruct | P3 | 9/30 (30,0 %) | 22/30 (73,3 %) | 1,425 / 0,876 s | 46,32 s |

Les blocs mesurés comptent zéro erreur technique. Le bloc P2 de Bonsai s’est arrêté pendant sa douzième requête, qui est enregistrée comme interrompue. Sur les 11 premières questions P2, tous les modèles ont rendu 11 réponses conformes. Bonsai en a réussi six, Qwen et Ministral trois chacun. La durée extrapolée depuis zéro est de 7 h 52 min 02 s pour Qwen et 4 h 52 min 29 s pour Ministral selon la même méthode. L’estimation historique de Bonsai est d’environ 67 h 05 d’inférence, calculée à partir de la latence moyenne de ses 41 réponses.

## Choix définitif du deuxième modèle

Le 25 novembre 2026, l’utilisatrice a validé le pilote et retenu **Ministral-3-3B-Instruct-2512** pour le deuxième benchmark complet.

- **Bonsai 27B** dépassait les contraintes de durée et de mémoire de la machine. L’estimation d’inférence était d’environ 67 h 05, et le pilote s’est arrêté après 41 réponses.
- **Qwen3 4B Instruct** présentait une durée active extrapolée de 7 h 52 min et une conformité P3 de 0/30.
- **Ministral 3 3B Instruct** offre le meilleur compromis entre durée, conformité et faisabilité matérielle parmi les pilotes. Il a terminé les 90 inférences sur la machine, avec une conformité de 100 % sur P1 et P2, de 73,3 % sur P3 et une durée active extrapolée de 4 h 52 min.

Les mesures Bonsai et Qwen restent dans les répertoires locaux de leurs pilotes pour la traçabilité. Les futurs marts Gold s’appuieront sur l’OBT de `dbt intermediate`, alimentée par les benchmarks complets validés de Gemma et Ministral.

## Benchmark complet Ministral du lot 4

Le 25 novembre 2026, le benchmark Ministral a démarré avec les 90 tentatives du pilote, à raison de 30 par prompt. Le plan comporte 5 260 nouvelles tentatives par prompt, soit 15 780 au total, dans l’ordre du manifeste du benchmark Gemma. Le contrôle au démarrage a retrouvé la configuration du pilote, y compris les empreintes des trois prompts. [Protocole et chemins de reprise](ARCHITECTURE.md#benchmark-complet-ministral-du-lot-4)

À 03 h 41, le client HTTP Windows a interrompu P3 après 3 159 réponses reçues, pilote compris. P1 et P2 étaient complets. Le journal LM Studio a compté 13 649 nouvelles réponses et trois échauffements avant l’arrêt. Les 13 échecs de transport qui suivent la dernière réponse ont été isolés pour permettre la reprise des positions sans requête reçue par LM Studio.

Le benchmark complet compte **15 870 réponses reçues**, dont 90 reprises du pilote. Les 15 780 nouvelles inférences couvrent exactement les 5 260 positions restantes de chacun des trois prompts.

| Mesure Ministral | `P1_choices` | `P2_expert` | `P3_expert_advanced` |
| --- | ---: | ---: | ---: |
| Réponses reçues | 5 290 | 5 290 | 5 290 |
| Bonnes réponses | 2 844 | 2 779 | 2 182 |
| Mauvaises réponses | 2 446 | 2 511 | 3 108 |
| Exactitude stricte | 53,76 % | 52,53 % | 41,25 % |
| Conformité | 5 278 (99,77 %) | 5 187 (98,05 %) | 4 166 (78,75 %) |
| Échecs de transport archivés | 0 | 0 | 13 |
| Positions sans réponse à la clôture | 0 | 0 | 0 |
| Latence HTTP moyenne | 0,736 s | 0,733 s | 1,092 s |
| Latence HTTP médiane | 0,711 s | 0,706 s | 0,753 s |
| Durée active du complément | 1 h 14 min 50 s | 1 h 14 min 43 s | 1 h 46 min 32 s |
| Durée active avec le pilote | 1 h 15 min 16 s | 1 h 15 min 10 s | 1 h 47 min 19 s |

P3 compte **1 124 sorties hors format**, dont 793 QCM et 331 vrai/faux. Le scoring strict les compte comme incorrectes. Les 13 échecs de transport P3 restent archivés dans `echecs_transport_reprise` avec leurs identifiants. LM Studio a confirmé que les 13 requêtes concernées n’avaient pas été reçues. La reprise a terminé les 2 131 positions P3 restantes avec Vulkan 2.80.1 et la configuration du pilote.

Le complément a pris **4 h 16 min 05 s** de temps actif. Avec les pilotes, le total est de **4 h 17 min 45 s** pour Ministral et **2 h 37 min 05 s** pour Gemma. Le temps actif inclut les écritures et exclut les échauffements, le chargement et la pause entre les deux segments de P3.

### Comparaison avec Gemma

| Prompt | Exactitude Gemma / Ministral | Conformité Gemma / Ministral | Latence moyenne Gemma / Ministral | Gemma seul correct / Ministral seul correct |
| --- | ---: | ---: | ---: | ---: |
| P1 | 54,12 % / 53,76 % | 100,00 % / 99,77 % | 0,463 / 0,736 s | 831 / 812 |
| P2 | 53,91 % / 52,53 % | 100,00 % / 98,05 % | 0,466 / 0,733 s | 884 / 811 |
| P3 | 52,04 % / 41,25 % | 98,96 % / 78,75 % | 0,522 / 1,092 s | 1 239 / 668 |

L’audit confirme 15 870 identifiants d’inférence distincts, l’ordre commun, l’identité des 90 mesures Pilote–Bronze–Silver, la concordance du journal et des Parquet et le scoring recalculé. Les 13 739 réponses présentes avant la reprise concordent champ par champ. L’audit LM Studio retrouve 15 784 appels, dont quatre échauffements, avec un seul message, `store=false` et sans référence à une réponse précédente. Les empreintes des 64 fichiers historiques Bronze et Silver contrôlés avant la reprise concordent. [Bronze](../data/bronze/benchmark_ministral_lot4/) · [Silver](../data/silver/benchmark_ministral_lot4/) · [Journal DuckDB](../data/silver/benchmark_ministral_lot4/benchmark.duckdb)

## Clôture du lot 4

L’utilisatrice a validé définitivement le benchmark Ministral et le comparatif avec Gemma. Les 13 échecs de transport restent archivés dans la table `echecs_transport_reprise` du journal DuckDB. Les phases dbt et Gold sont hors de cette clôture. [Journal d’audit](../data/silver/benchmark_ministral_lot4/benchmark.duckdb)

## Décision initiale de consolidation

Les sources disponibles sont les sept Parquet validés du Silver préparé. Le corpus OpenTDB contient 5 290 lignes et 10 colonnes. Les six Parquet des benchmarks Gemma et Ministral contiennent chacun 5 290 réponses pour une combinaison modèle–prompt. Le Bronze OpenTDB et LLM reste intact. [Chemins des sept sources](ARCHITECTURE.md#sources-du-silver-préparé)

La décision initiale classait le résultat de la consolidation en « Silver consolidé ». Elle fixait le grain à une ligne par combinaison question × modèle × prompt et le périmètre aux six benchmarks complets, réponses hors format comprises. L’alignement D42 réaffecte cette OBT à `dbt intermediate` avec les mêmes sources et règles. [Décision initiale et remplacement](DECISIONS.md#dec-032--construire-une-one-big-table-dans-le-silver-consolidé)

## Construction initiale et contrôles de l’OBT

Les étapes 5 à 7, validées au jalon `e76715e`, ont produit `silver.obt_silver` dans la base locale `data/silver/obt_silver.duckdb`. `dbt build` a réussi avec dbt Core `1.12.7`, dbt-duckdb `1.11.1` et DuckDB `2.0.1` dans la `.venv` du projet. Le build a matérialisé 8 vues et 1 table et validé les 27 tests de données, sans avertissement ni erreur. Cette base est la référence du reclassement D42.

| Contrôle | Résultat |
| --- | --- |
| Volume et schéma | 31 740 lignes et 22 colonnes. Seul `question_id` est fusionné. |
| Couverture | 5 290 questions distinctes, 6 inférences par question et 5 290 lignes dans chacune des 6 combinaisons modèle–prompt. |
| Clés | 31 740 UUID d’inférence distincts, zéro doublon du triplet et zéro résultat orphelin. |
| Concordance | Zéro écart de valeur ou de multiplicité entre les projections de l’OBT et les sept Parquet. Le scoring strict recalculé concorde avec les valeurs historiques. |
| Réponses et `NULL` | 1 294 réponses hors format avec `ai_answer` à `NULL`, dont quatre réponses brutes vides. `error_type` et `error_message` sont conservés avec 31 740 valeurs `NULL` chacun. |
| Intégrité des sources | Les SHA-256 des 85 fichiers Bronze et Silver préexistants concordent avant et après le build. |

## Alignement sur le schéma D42

Les sept Parquet préparés par Python forment Silver et constituent le point de départ du lignage dbt. La base locale `data/trivial_pursuit.duckdb` regroupe les sept vues dans `staging`, la vue d’union et la table `intermediate.obt_silver`. Le schéma `gold` est réservé aux futurs marts métier consommables par Power BI, Qlik, un environnement de data science ou une application métier. [Décision D42](DECISIONS.md#dec-034--appliquer-la-séparation-des-couches-du-cours-d42)

`dbt build` a réussi de nouveau pour les 9 modèles et 27 tests, avec zéro avertissement et zéro erreur. La relecture confirme 31 740 lignes, 22 colonnes, 5 290 questions distinctes, six résultats par question, 5 290 lignes pour chacune des six combinaisons modèle–prompt et 1 294 réponses hors format conservées. Elle retrouve zéro doublon sur le grain et zéro résultat orphelin.

La comparaison en lecture seule avec `silver.obt_silver` dans la base historique confirme le même ordre de colonnes, les mêmes types et la même nullabilité. Les `EXCEPT ALL` dans les deux sens retournent chacun zéro ligne. Les tests de source confirment la concordance des valeurs, scores, statuts et latences, `NULL` compris. Les empreintes SHA-256 des 86 fichiers Bronze et Silver préexistants concordent, dont les sept Parquet et la base de référence.

La documentation dbt de ce jalon exposait le lignage jusqu’à `intermediate.obt_silver`. Les résultats de ce build sont dans `dbt/target/build_run_results.json`. [Dictionnaire, qualité et lignage](ARCHITECTURE.md#dictionnaire-des-colonnes-de-lobt) · [Procédure](../README.md#construire-le-pipeline-dbt-et-consulter-le-lignage)

## Publication collaborative des données définitives

Le dépôt versionne les douze Parquet définitifs de Gemma et Ministral, soit six en Bronze et six en Silver. Les huit fichiers ajoutés correspondent à Gemma P3 et aux trois prompts de Ministral dans les deux couches. Avec le corpus OpenTDB final, les six exports Silver donnent les sept sources du projet dbt et couvrent 31 740 résultats de benchmark. Le CSV Bronze OpenTDB, les jalons Parquet, les rapports qualité et les scripts sont également disponibles dans le dépôt. [Inventaire des données publiées](../README.md#jeux-de-données-disponibles-sur-github) · [Procédure dbt](../README.md#construire-le-pipeline-dbt-et-consulter-le-lignage)

## Lot 8 · Construction de Gold

Les sept marts sont matérialisés dans le schéma `gold` de `data/trivial_pursuit.duckdb`. Leur lignage part de `intermediate.obt_silver` et `mart_category_gap` réutilise `mart_category`. La définition des grains, des unités et des mesures figure dans l’architecture. [Marts Gold](ARCHITECTURE.md#gold-et-restitution)

| Modèle et prompt | Correctes | Incorrectes conformes | Hors format | Réussite | Conformité | Latence moyenne |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Gemma P1 | 2 863 | 2 427 | 0 | 54,12 % | 100,00 % | 0,463 s |
| Gemma P2 | 2 852 | 2 438 | 0 | 53,91 % | 100,00 % | 0,466 s |
| Gemma P3 | 2 753 | 2 482 | 55 | 52,04 % | 98,96 % | 0,522 s |
| Ministral P1 | 2 844 | 2 434 | 12 | 53,76 % | 99,77 % | 0,736 s |
| Ministral P2 | 2 779 | 2 408 | 103 | 52,53 % | 98,05 % | 0,733 s |
| Ministral P3 | 2 182 | 1 984 | 1 124 | 41,25 % | 78,75 % | 1,092 s |

Chaque comparaison couvre 5 290 paires. Pour P3−P1, Gemma compte 313 gains et 423 pertes (−2,08 points de réussite), et Ministral 155 gains et 817 pertes (−12,51 points). Sur les six configurations, 1 379 questions sont toujours correctes, 1 278 toujours incorrectes et 2 633 ont un résultat mixte.

Le `dbt build` intégral en base de vérification a réussi pour 16 modèles et 41 tests. Le build ciblé dans la base de travail a matérialisé les sept marts et exécuté leurs 14 tests, puis `dbt test` a confirmé les 41 tests, dont les 27 tests historiques. Le catalogue confirme les sept tables et leurs dimensions attendues. La documentation statique du lignage a été régénérée dans `dbt/target/static_index.html`.

Les SHA-256 des 86 fichiers Bronze et Silver concordent. Les définitions des huit vues et de l’OBT, leurs schémas et les valeurs de l’OBT ont été comparés avant et après le build ciblé, avec zéro écart dans les deux sens. L’ancien `data/gold/` ne contenait qu’un `.gitkeep` et le projet dbt écrit dans `data/trivial_pursuit.duckdb`. Ce répertoire vide a été retiré. [Procédure de reconstruction](../README.md#construire-le-pipeline-dbt-et-consulter-le-lignage)

## Lot 8 bis · Complément méthodologique Gold

Dans `data/trivial_pursuit.duckdb`, `mart_difficulty` compte 54 lignes × 9 colonnes, `mart_question_type` 12 × 9 et `mart_question_outcomes` 5 290 × 14. Le taux du hasard est de 25 % pour les 4 501 QCM et de 50 % pour les 789 vrai/faux par configuration. [Grains et définitions](ARCHITECTURE.md#gold-et-restitution)

| Difficulté | QCM | Vrai/faux | Hasard pondéré | Plage des écarts au hasard sur les six configurations |
| --- | ---: | ---: | ---: | ---: |
| Facile | 1 405 | 359 | 30,09 % | +16,74 à +33,97 points |
| Intermédiaire | 2 091 | 333 | 28,43 % | +10,92 à +23,30 points |
| Difficile | 1 005 | 97 | 27,20 % | +9,28 à +22,44 points |

| Configuration | Écart QCM (points) | Conformité QCM | Écart vrai/faux (points) | Conformité vrai/faux |
| --- | ---: | ---: | ---: | ---: |
| Gemma P1 | +29,01 | 100,00 % | +4,75 | 100,00 % |
| Gemma P2 | +28,83 | 100,00 % | +4,37 | 100,00 % |
| Gemma P3 | +27,30 | 98,78 % | +0,57 | 100,00 % |
| Ministral P1 | +28,52 | 99,98 % | +5,13 | 98,61 % |
| Ministral P2 | +27,70 | 99,96 % | +1,58 | 87,20 % |
| Ministral P3 | +17,41 | 82,38 % | −15,40 | 58,05 % |

Le comptage de l’OBT confirme 308 consensus incorrects parmi les 1 278 questions `all_incorrect`. Ils se répartissent en 207 QCM et 101 vrai/faux. Les autres effectifs restent à 1 379 questions `all_correct` et 2 633 `mixed`.

Le `dbt build` complet en base de vérification a validé 16 modèles et 41 tests, dont les 27 historiques. Le build ciblé dans la base de travail a validé les trois tables modifiées et leurs six tests. Les totaux par difficulté concordent avec la ventilation, les taux et la conformité avec l’OBT, et le consensus avec un comptage indépendant. Les SHA-256 des 86 fichiers Bronze et Silver concordent. L’OBT et les quatre autres marts conservent leurs schémas et toutes leurs valeurs, et les définitions des huit vues restent identiques. La documentation du lignage a été régénérée dans `dbt/target/static_index.html`. [Procédure de reconstruction](../README.md#construire-le-pipeline-dbt-et-consulter-le-lignage)

## Lot 9 · Dashboard Streamlit

Les sept marts totalisent 5 584 lignes. Le dashboard les lit dans `data/trivial_pursuit.duckdb` en lecture seule et présente les 5 290 questions et 31 740 réponses du benchmark dans quatre onglets. Les taux et latences proviennent de Gold. Les effectifs de questions suivent la sélection. [Vues, filtres et mesures](../specifications/DASHBOARD.md) · [Lancement](../README.md#lancer-le-dashboard-streamlit)

| Contrôle | Valeur vérifiée dans l’application |
| --- | --- |
| Gemma P1 | 54,12 % de précision, 100,00 % de conformité, 0,463 s |
| Ministral P3 | 41,25 % de précision, 78,75 % de conformité, 1,092 s |
| Précision P3−P1 | −2,08 points pour Gemma et −12,51 points pour Ministral |
| Ministral P3, vrai/faux | 34,60 % de réussite, −15,40 points sous le hasard, 58,05 % de conformité |
| Questions | 1 379 réussies par les six configurations, 1 278 ratées par les six et 2 633 mixtes |
| Échecs communs | 308 consensus incorrects (207 QCM et 101 vrai/faux), 970 autres échecs. Part des consensus de 24,10 %. |

Cinq tests automatisés Streamlit couvrent les dimensions des sept marts, les valeurs de référence, les graphiques des sept vues, les filtres, la recherche, les sélections vides et la réinitialisation. Le serveur local a répondu en HTTP 200. Chromium a vérifié la navigation et les interactions sur le dashboard, et les captures ont été inspectées à 1 440 × 1 050 pixels. Les 16 modèles et 41 tests dbt correspondent au jalon Gold validé. Les empreintes SHA-256 des 263 fichiers de `data/` et `dbt/`, base DuckDB comprise, concordent avant et après le lot 9.

## Lot 9 bis · Refonte ergonomique du dashboard

Le bandeau introduit le benchmark et quatre questions guident le parcours. Les filtres courts deviennent des boutons segmentés à choix unique ou multiples selon le grain. Les catégories restent accessibles par liste déroulante. Les cartes présentent des valeurs Gold et les encadrés « À retenir » suivent les filtres de la vue. La comparaison par catégorie propose aussi des points reliés, et les cartes thermiques affichent les taux dans les cellules. La fiche ludique sélectionne une question parmi les résultats filtrés et masque sa réponse jusqu’au clic. [Parcours et filtres](../specifications/DASHBOARD.md) · [Choix de conception](DECISIONS.md#dec-039--guider-lexploration-du-dashboard)

Les cinq tests de non-régression et le test de la fiche interactive passent. Les contrôles couvrent l’exactitude des KPI, les filtres, les sélections vides, la réinitialisation par vue et le retour à une réponse masquée quand la question change. La vérification Chromium à 1 440 pixels de largeur a produit une capture par onglet et contrôlé les filtres, la réinitialisation au clavier, la comparaison par catégorie, la carte thermique, le repère du hasard et la révélation d’une réponse avec consensus. Les SHA-256 des 263 fichiers de `data/` et `dbt/`, base DuckDB comprise, concordent avant et après le lot 9 bis.

Après la validation visuelle, le bandeau présente les six chiffres clés vérifiés dans Gold et indique que les questions originales sont en anglais. Les textes expliquent la sélection de plusieurs boutons, les six configurations et l’unité des écarts. Les mesures sont présentées comme un taux de bonnes réponses et un temps moyen de réponse. La carte de comparaison nomme une hausse, une baisse ou un taux inchangé selon le signe du meilleur écart parmi les résultats filtrés. Les six tests Streamlit existants ont réussi après ces finitions, et le contrôle des empreintes de `data/` et `dbt/` a de nouveau confirmé leur intégrité.

## Analyse exploratoire par familles OpenTDB

L’analyse SQL a porté exclusivement sur `gold.mart_category` dans DuckDB en lecture seule. Elle a réuni les dix catégories préfixées `Entertainment: ` sous Entertainment, puis les catégories Science & Nature, Computers, Mathematics et Gadgets (identifiants 17, 18, 19 et 30) sous Science. Les dix autres catégories sont restées individuelles. Chaque catégorie appartient à une seule des **12 familles**. Le taux de chaque groupe est `100 × SUM(correct_count) / SUM(response_count)`. Pour chacune des six configurations, la somme des familles retrouve exactement les effectifs et les bonnes réponses du mart. Aucune table persistante n’a été créée. L’empreinte de DuckDB concorde avant et après, et l’analyse n’a modifié ni le pipeline ni le dashboard.

- **Science** atteint le quatrième rang dans les six configurations, alors que Science & Nature figure dans le trio de tête des catégories détaillées dans chacune d’elles. À P3, l’avance de Gemma atteint 9,05 points de pourcentage dans la famille, avec 13,54 points en Computers et 1,27 point en Mathematics.
- **Entertainment** représente 2 803 questions sur 5 290 et se classe parmi les deux dernières familles des six configurations, y compris après retrait de Video Games. Cette catégorie compte 1 186 questions, soit 42,31 % de la famille. Son retrait relève les six taux de 3,37 à 5,34 points de pourcentage. L’écart Gemma − Ministral à P3 passe de 12,45 à 12,24 points.
- **Comparaison des prompts.** Art arrive en tête pour les deux modèles à P1 et P2, puis Mythology à P3. À P3, Gemma devance Ministral dans les 12 familles et les 24 catégories. Entertainment représente 349 des 571 bonnes réponses supplémentaires de Gemma à P3, soit 61,12 % de l’écart net sur ce prompt.

Les résultats décrivent la composition réelle du corpus OpenTDB. Les effectifs inégaux et parfois faibles rendent les rangs descriptifs. Le mart agrégé ne permet ni de tester les écarts question par question ni de séparer les réponses fausses des réponses hors format. Une future hiérarchie pourrait ajouter une vue de synthèse par famille avec accès aux catégories d’origine et affichage des effectifs à chaque niveau. [Décision exploratoire](DECISIONS.md#dec-040--documenter-le-regroupement-exploratoire-opentdb)
