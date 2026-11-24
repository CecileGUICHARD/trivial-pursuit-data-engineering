# État d’avancement

Mis à jour le 24 novembre 2026. La collecte Bronze est vérifiée. La préparation de Silver attend la validation des règles de traitement des questions répétées.

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

La comparaison des libellés nettoyés sans tenir compte de la casse retrouve les quatre paires détectées par `exploration.py`.

| Question | Différence entre les deux lignes |
| --- | --- |
| Apparition du type Fée dans Pokémon | Catégorie différente, mêmes choix |
| Nombre de côtés d’un heptagone | Mauvaises réponses proposées différentes, même bonne réponse |
| Début de la Révolution française | Bonne réponse attendue à deux niveaux de précision (`May 05 1789` ou `1789`), autres choix différents |
| Auteur de la Joconde | Mauvaises réponses proposées différentes, même bonne réponse |

## Prochain jalon

Valider la règle de traitement des quatre paires avant d’implémenter la préparation de Silver. La proposition consiste à conserver les 5 299 lignes et à signaler les huit variantes. Les autres [choix à arbitrer](ARCHITECTURE.md#choix-à-arbitrer) restent ouverts. Les inférences, les modèles dbt, les indicateurs Gold et l’application Streamlit restent à réaliser.
