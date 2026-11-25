# Consignes pour les agents IA

Le projet est un benchmark de LLM locaux pour le cours D42 du M1 Big Data & IA. L’objectif pédagogique principal est de démontrer la maîtrise du Data Engineering.

## Contexte et suivi

- Lire le [README](README.md) pour comprendre le projet et [CURRENT.md](documentation/CURRENT.md) au début de chaque session.
- Vérifier les fichiers existants avant toute création ou modification. Consulter [ARCHITECTURE.md](documentation/ARCHITECTURE.md) avant tout changement technique ou structurel important.
- Mettre à jour `CURRENT.md` après chaque tâche significative et `ARCHITECTURE.md` quand les choix techniques évoluent. Signaler toute contradiction entre le code et les documents.
- Mettre à jour le [registre `DECISIONS.md`](documentation/DECISIONS.md) après chaque nouvel arbitrage validé. Si l’arbitrage fait évoluer un choix antérieur, conserver la notice d’origine et indiquer son statut ainsi que le lien vers la nouvelle décision.

## Développement et qualité

- Respecter l’architecture en médaillon et les niveaux dbt `staging`, `intermediate` et `marts`. Utiliser des scripts Python, des modèles SQL dbt et Streamlit. Écarter les notebooks Jupyter.
- Préserver les données Bronze originales. Faire valider les règles avant toute suppression ou exclusion de questions. Vérifier les données avant et après chaque transformation.
- Rapporter uniquement des données, des résultats et des mesures constatés, et des tests réellement exécutés.
- Utiliser des chemins portables, notamment avec `pathlib`. Réutiliser `.venv` et justifier toute nouvelle dépendance.
- Justifier les choix techniques importants pour la soutenance. Soumettre les arbitrages à l’utilisatrice et attendre sa validation avant de développer les étapes suivantes.

## Pilote du benchmark

- Préparer et contrôler Silver avant de démarrer les inférences. Utiliser le manifeste du Silver définitif `data/silver/pilot_lot2/pilot_question_ids.parquet` pour rejouer les mêmes questions dans le même ordre.
- Utiliser Gemma 4 E2B via LM Studio et les deux prompts `P1_choices` et `P2_expert`. Garder les propositions, leur ordre et les paramètres du modèle identiques. L’ajout du rôle d’expert est la seule différence entre les prompts.
- Enregistrer les réponses brutes, latences, configurations et erreurs techniques dans une table Bronze par modèle et prompt. Produire le Silver structuré à partir du Bronze et des réponses attendues. Calculer les métriques à partir des mesures réelles et réutiliser les réponses du pilote lors de la reprise. [Protocole de mesure](documentation/ARCHITECTURE.md#benchmark)
- Attendre la validation de l’utilisatrice avant le benchmark complet ou le choix d’un deuxième modèle.

## Git et GitHub

- Respecter `.gitignore`. Laisser par défaut hors de Git les données générées, les bases DuckDB et `.venv`. Garder les jetons, mots de passe et autres secrets hors du dépôt et de toute publication.
- Proposer un commit après chaque jalon fonctionnel, testé et documenté. Vérifier `git status`, `git diff --stat` et `git diff --check`, puis exécuter les tests pertinents. Présenter les fichiers concernés, les résultats des vérifications et un message de commit explicite en français.
- Demander l’autorisation avant tout `git add`, `git commit` ou `git push`.

## Communication

- Répondre en français, de façon concise, précise et pédagogique. Expliquer les modifications et leur utilité, puis signaler les décisions qui nécessitent un arbitrage.
