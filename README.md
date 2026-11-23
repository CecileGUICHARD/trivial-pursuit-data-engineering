Trivial Pursuit - Benchmark de LLM locaux
Projet de Data Engineering - M1 (23 au 26 novembre 2026)
Livrables attendus : depot GitHub, application Streamlit et presentation orale.
1. Objectif du projet
Concevoir un pipeline de donnees complet pour collecter des questions de culture generale via Open Trivia Database (OpenTDB), les preparer, interroger des modeles d'IA locaux et analyser leurs performances.

L'objectif pedagogique principal est de demontrer des competences en Data Engineering (extraction, qualite, transformation, modelisation, stockage, automatisation et restitution). Le benchmark des LLM constitue le cas d'usage.
Axes d'analyse retenus
- Axe 1 - Comparaison des modeles : precision globale, temps de reponse moyen et median, respect du format attendu, stabilite des reponses et erreurs communes.
- Axe 2 - Influence du prompt : P0 (question directe, reference), P1 (role d'expert en culture generale), P2 (droit a repondre " INCONNU "), P3 (indication du domaine).
- Axe 3 - Categories et difficulte : classement des themes, performance par niveau, categorie x difficulte et categorie x prompt.
Premier modele choisi : Gemma 4 E2B. Deuxieme modele : a definir.
2. Source des donnees
- Source : Open Trivia Database
- API publique : https://opentdb.com/api.php ; aucune cle requise.
- Exemple de requete : https://opentdb.com/api.php?amount=50
- Format : JSON ; licence annoncee : CC BY-SA 4.0.
- Contraintes : au maximum 50 questions par appel et un appel toutes les 5 secondes par adresse IP ; jetons de session pour eviter les repetitions pendant la collecte.
Champ API	Description
type	QCM (multiple) ou vrai/faux (boolean)
difficulty	easy, medium ou hard
category	Categorie de culture generale
question	Texte de la question
correct_answer	Reponse correcte
incorrect_answers	Liste des reponses incorrectes


3. Environnement et organisation
Developpement dans Debian (WSL) avec VS Code. Python est execute dans un environnement virtuel .venv ; les bibliotheques utilisees a ce stade sont requests et pandas.
trivial_pursuit/
|-- .venv/                     # Environnement virtuel local
|-- collect_opentdb.py        # Extraction test API -> CSV
|-- exploration.py            # Controles qualite / exploration
|-- README.md
|-- data/
|   |-- bronze/
|   |   \-- questions_raw.csv
|   |-- silver/               # Prevu : donnees preparees en Parquet
|   \-- gold/                 # Prevu : indicateurs du benchmark
\-- notebooks/
Reproduire l'extraction test
Dans le terminal Debian, depuis la racine du projet :
python3 -m venv .venv           # A faire une seule fois
source .venv/bin/activate
python -m pip install requests pandas
python collect_opentdb.py       # Collecte de 50 questions
python exploration.py           # Exploration du CSV
4. Travail realise - 23 novembre 2026
4.1. Preparation
- Creation du projet ~/projets/trivial_pursuit dans Debian.
- Ouverture du projet dans VS Code connecte a WSL.
- Creation des repertoires data/bronze, data/silver, data/gold, notebooks.
- Creation et activation de .venv, puis installation de requests et pandas.
4.2. Premiere extraction (Bronze)
Le script collect_opentdb.py effectue une requete HTTP a OpenTDB (amount=50), verifie les codes de retour, extrait results, cree un DataFrame Pandas et ecrit le CSV data/bronze/questions_raw.csv (utf-8-sig). La liste incorrect_answers est enregistree sous forme de texte JSON dans une colonne CSV.

Resultat : 50 questions extraites. Les donnees restent brutes a ce stade : pas de decodage HTML, pas de filtrage sur le type de question.
4.3. Controles qualite de l'extraction test
Executes avec exploration.py (Pandas) :
Controle	Resultat
Nombre de lignes	50
Nombre de colonnes	6
Valeurs manquantes	0
Doublons stricts sur la colonne question	0
Questions QCM (multiple)	43
Questions vrai/faux (boolean)	7
Categories representees	15


Difficultes : 15 easy, 19 medium, 16 hard.

Repartition par categorie :
Categorie (valeur brute)	Nombre
Entertainment: Video Games	7
Entertainment: Music	6
General Knowledge	6
Entertainment: Books	5
History	4
Geography	4
Animals	3
Entertainment: Film	3
Entertainment: Cartoon &amp; Animations	2
Science: Computers	2
Entertainment: Board Games	2
Entertainment: Japanese Anime &amp; Manga	2
Entertainment: Television	2
Science &amp; Nature	1
Celebrities	1


4.4. Enseignements de l'exploration
- La connexion API et l'export CSV fonctionnent.
- Les six colonnes sont presentes et non nulles dans le lot teste.
- Les types multiple et boolean devront etre distingues : leur probabilite de bonne reponse au hasard differe.
- Des caracteres encodes en HTML, comme &amp;, devront etre decodes en Silver, sans alterer les donnees Bronze.
- Aucun doublon strict sur l'enonce dans ces 50 questions ; il faudra renforcer le controle sur le dataset complet.
- Limite : ce lot de 50 questions est un test technique, non un echantillon representatif pour conclure sur les modeles.
5. Architecture cible (a realiser)
API OpenTDB (JSON)
     | extraction Python
BRONZE : questions_raw.csv (donnees sources)
     | nettoyage, normalisation et preparation des QCM
SILVER : fichiers Parquet + reponses brutes des LLM
     | transformations SQL avec dbt : staging -> intermediate -> mart
GOLD : indicateurs dans DuckDB
     |
Streamlit : tableau de bord interactif
La granularite prevue pour les evaluations est une ligne par question x modele x prompt x execution : elle permettra de comparer les modeles, les prompts et les repetitions, sans ecraser les resultats anterieurs.
6. Suivi d'avancement
- [x] Configurer Debian/WSL, VS Code et .venv.
- [x] Interroger l'API et creer questions_raw.csv (50 questions).
- [x] Explorer la structure et effectuer les premiers controles qualite.
- [ ] Collecter toutes les questions accessibles via l'API, avec gestion des jetons, du debit, des erreurs et des reprises.
- [ ] Controler le dataset complet et preparer les fichiers Parquet Silver.
- [ ] Modeliser les tables questions, modeles, prompts et resultats d'inference.
- [ ] Executer les tests avec Gemma 4 E2B puis un deuxieme modele.
- [ ] Developper les transformations et les tests dbt ; documenter le lignage.
- [ ] Produire les indicateurs Gold avec DuckDB et le dashboard Streamlit.
- [ ] Preparer le depot GitHub et la presentation orale.
Note : aucun benchmark de LLM n'a encore ete execute. Toutes les statistiques ci-dessus correspondent exclusivement a la premiere extraction de 50 questions.