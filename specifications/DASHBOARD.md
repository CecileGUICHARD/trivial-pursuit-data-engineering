# Dashboard du benchmark

L’application Streamlit présente les modèles Gemma 4 E2B et Ministral 3 3B sur les mêmes questions OpenTDB. Elle lit les sept marts du schéma `gold` de `data/trivial_pursuit.duckdb` en lecture seule. [Installation et lancement](../README.md#lancer-le-dashboard-streamlit) · [Dictionnaire des marts](../dbt/models/marts/marts.yml)

Le bandeau pose la question centrale du benchmark et donne son périmètre. Il affiche 5 290 questions, 24 catégories, 31 740 réponses, 2 modèles, 3 prompts et 6 configurations. Les questions OpenTDB originales sont en anglais. Quatre onglets guident l’exploration avec des cartes récapitulatives et des encadrés « À retenir » qui suivent la sélection. Le turquoise identifie Gemma et l’orange Ministral. Le repère gris représente un choix effectué au hasard.

| Onglet et vue | Source Gold | Filtres | Restitution |
| --- | --- | --- | --- |
| Le duel des IA | `mart_performance` | Modèles, prompts | Barres groupées de `correct_pct`, `compliance_pct` et `avg_response_time_s`. Répartition empilée à 100 % avec `correct_pct`, `incorrect_conforming_pct` et `out_of_format_pct`. |
| Le pouvoir des prompts | `mart_prompt_comparison` | Modèles, paires orientées P2−P1, P3−P1, P3−P2 | Barres de `gain_count` et `loss_count`, avec pertes du côté négatif. Graphiques des trois écarts `success_delta_pp`, `compliance_delta_pp` et `response_time_delta_s`. Tableau repliable des six mesures avant et après. |
| Les domaines de prédilection · Performance par catégorie | `mart_category` | Modèles, prompts, catégories | Classements horizontaux de `success_pct` par configuration et cartes thermiques catégorie × prompt par modèle, avec le taux affiché dans chaque cellule. |
| Les domaines de prédilection · Écarts entre modèles | `mart_category_gap` | Prompts, catégories | Points reliés pour `gemma_success_pct` et `ministral_success_pct`, puis barres de `success_gap_pp` distinctes par prompt. Un écart positif favorise Gemma, un écart négatif favorise Ministral. `is_tie` repère les égalités. |
| Domaines · Difficulté | `mart_difficulty` | Modèles, prompts, difficultés, un type parmi `all`, `multiple` et `boolean` | `success_pct` avec repère `chance_pct` et barres divergentes de `above_chance_pp`. Le total `all` utilise la référence pondérée fournie par Gold. |
| Domaines · Type de question | `mart_question_type` | Modèles, prompts, types | `success_pct` avec repère `chance_pct`, `above_chance_pp` et `compliance_pct`. La référence est celle d’un choix uniforme parmi les réponses valides, soit 25 % en QCM et 50 % en vrai/faux. |
| Les questions pièges | `mart_question_outcomes` | Catégories, difficultés et types pour la synthèse. Résultat, consensus et recherche dans le libellé pour la fiche et le tableau. | Quatre cartes. Distribution des trois résultats, décomposition des échecs communs, part des consensus parmi ces échecs et effectifs des consensus par type. Fiche individuelle et tableau repliable avec effectif filtré. |

Les graphiques conservent les configurations séparées et affichent les mesures au grain de leur mart. Le taux de bonnes réponses est présenté à deux décimales, et le temps moyen de réponse à trois décimales en secondes. Les écarts de taux s’expriment en points de pourcentage (pp). Passer de 50 % à 55 % représente une hausse de 5 pp. Dans la comparaison des prompts, le libellé de la première carte s’adapte au signe de la variation la plus favorable parmi les lignes sélectionnées.

Les filtres affichent « P1 — Consigne simple », « P2 — Rôle d’expert » et « P3 — Expert et analyse ». Une aide indique les boutons qui peuvent être sélectionnés ensemble. Un bouton réinitialise les filtres de la vue. Une liste de catégories vide correspond à toutes les catégories. Un message signale une sélection sans résultat.

## Détail des questions pièges

Chaque question a été posée aux deux modèles, chacun avec les trois consignes, soit six configurations. La synthèse s’appuie sur les résultats de ces six configurations et dépend des trois filtres de question. Les filtres de détail affinent la fiche et le tableau. Le consensus incorrect fait partie de `all_incorrect`. Sa part correspond à l’effectif des consensus divisé par celui des échecs communs dans la synthèse filtrée. Cette part est indisponible quand la sélection ne contient aucun échec commun.

La fiche propose une question à la fois et affiche ses choix dans l’ordre du benchmark. Le bouton « Révéler la réponse » montre la bonne réponse, sa valeur attendue dans le benchmark et le consensus incorrect quand il existe. Changer de question ou réinitialiser la vue masque à nouveau la réponse.

Le tableau affiche `question`, `category`, `difficulty`, `type`, `correct_answer`, `answer_choices`, `expected_answer`, `same_wrong_answer`, `outcome` et `unanimous_wrong`. La valeur commune `same_wrong_answer` est affichée sous sa forme brute, soit la lettre du choix ou `True`/`False` selon le format du benchmark. La recherche est littérale et insensible à la casse.
