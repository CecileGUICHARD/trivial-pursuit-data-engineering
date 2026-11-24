from argparse import ArgumentParser
from collections import Counter, defaultdict
import csv
from hashlib import sha256
from html import unescape
import json
from pathlib import Path
import re
from string import ascii_uppercase
from tempfile import TemporaryDirectory
from unicodedata import category, normalize

import duckdb
import pandas as pd


RACINE = Path(__file__).resolve().parent
BRONZE = RACINE / "data" / "bronze" / "questions_raw.csv"
SILVER = RACINE / "data" / "silver" / "questions_clean.parquet"
QUESTIONS_DEDOUBLONNEES = SILVER.with_name("questions_dedoublonnees.parquet")
AVANT_DEDOUBLONNAGE = SILVER.with_name("questions_avant_dedoublonnage.parquet")
QUESTIONS_NORMALISEES = SILVER.with_name("questions_normalisees.parquet")
QUESTIONS_BENCHMARK = SILVER.with_name("questions_benchmark.parquet")
MANIFESTE_PILOTE = SILVER.with_name("pilot_question_ids.parquet")
CLASSEMENT = SILVER.with_name("classement_diagnostic_anglais_lot2.csv")
CANDIDAT = SILVER.parent / "candidat_final_5290"
RAPPORT_QUALITE = "rapport_qualite_silver.csv"
SEED_PILOTE = 42
COLONNES_STRATES = ("category", "difficulty", "type")
COLONNES_TEXTE = (*COLONNES_STRATES, "question", "correct_answer")
NOMBRE_CHOIX = {"boolean": 2, "multiple": 4}
COLONNES_SOURCE = ("type", "difficulty", "category", "question", "correct_answer", "incorrect_answers")
SCHEMA_SOURCE = tuple(zip(COLONNES_SOURCE, ("VARCHAR",) * 5 + ("VARCHAR[]",)))
SCHEMA_FINAL = (
    *SCHEMA_SOURCE,
    ("question_id", "VARCHAR"),
    ("answer_choices", "VARCHAR[]"),
    ("expected_answer", "VARCHAR"),
    ("category_id", "INTEGER"),
)
NOMBRE_QUESTIONS = 5295
NOMBRE_QUESTIONS_FINAL = 5290
EMPREINTE_BRONZE = "cd2b093512002f0e58c0c9f04fb1bc84ee7168d86c7b6e1f8e4d4a1f60e73d99"
EMPREINTE_NORMALISEES = "5434aa0bea5441f11e66882ec666d86479b34399bbfe9b03e8ddb68253238ee7"
EMPREINTE_CLASSEMENT = "de05d1f34af9fb408d3c757a3fa8f3773434679993a582ca44da71150bf06d61"
EMPREINTE_SILVER_INITIAL = "0274c8a547a78b4a6673dca152144988403d9a1cd1b6425ebba33d1e349da736"

# CSV GARDER/EXCLURE validé par l’utilisatrice. Chaque paire donne le couple
# (question_id, libellé exact) à garder, celui à exclure, puis le motif fourni.
ARBITRAGES_DOUBLONS_SILVER = (
    (
        ("42b00d831db5acb82c7972c2cab81969ac5e1b6506645b7fdf910821c2f67812",
         '"Nephelococcygia" is the practice of doing what?'),
        ("864ac6d95a7aeebf68e4f0cdcc105d2bbccd085a938b511f3ca8873c797410b0",
         "Nephelococcygia is the practice of doing what?"),
        "Même catégorie, mêmes réponses, seuls les guillemets diffèrent. Version avec le mot entre guillemets gardée.",
    ),
    (
        ("295100cf268de04bb8bb3521ed1b878fe6ce87f252ff18ca53afad1af602a9c0",
         "If you planted the seeds of Quercus robur, what would grow?"),
        ("984b1b65b94a3d49f3b9f279c7f7085bacf6f4e08c2839775732c2d75a9ee900",
         "If you planted the seeds of Quercus robur what would grow?"),
        "Même question et bonne réponse. Version gardée sans faute (Vegetables, pas Vegtables) et bien ponctuée.",
    ),
    (
        ("f5b08e7a2540194b30d078443ee24c1394a582b899b4434f5f460f41dfb74c14",
         "What is the hottest planet in the Solar System?"),
        ("72d3336c3036bfae3d341a4cc0e0a3782441aa74d751f44d95997115a95ac744",
         "What is the hottest planet in the solar system"),
        "Même catégorie, mêmes réponses dans un autre ordre. Version gardée bien ponctuée.",
    ),
    (
        ("802293658c82b53d8e553e5f3779f50b0a16bae0f0ca0fbb7b6e9995de27be48",
         "What is the largest country in the world?"),
        ("85f36f28271c2d6bc9eb2dcc0545b7dd9fd9e12f90921070167eeb8cb7d071ec",
         "What is the largest country in the world ?"),
        "Même question. Version gardée bien ponctuée, réponse Russia, United States plus crédible que Brazil.",
    ),
    (
        ("b8dcf6ccc470dd3875a6e10f5b0841a24731ea52943d76f4e2ab0b3516016e47",
         "Who painted The Starry Night?"),
        ("0771af17087fe4f3c9163d7b1e318f0fca9681ac7de24f40bf081bacf566c61a",
         'Who painted "The Starry Night"?'),
        "Même question et bonne réponse (Vincent van Gogh). Choix de l'équipe : version sans guillemets.",
    ),
)

# Catalogue publié à https://opentdb.com/api_category.php, vérifié le 24 novembre 2026.
CATEGORIES_OPENTDB = {
    "General Knowledge": 9,
    "Entertainment: Books": 10,
    "Entertainment: Film": 11,
    "Entertainment: Music": 12,
    "Entertainment: Musicals & Theatres": 13,
    "Entertainment: Television": 14,
    "Entertainment: Video Games": 15,
    "Entertainment: Board Games": 16,
    "Science & Nature": 17,
    "Science: Computers": 18,
    "Science: Mathematics": 19,
    "Mythology": 20,
    "Sports": 21,
    "Geography": 22,
    "History": 23,
    "Politics": 24,
    "Art": 25,
    "Celebrities": 26,
    "Animals": 27,
    "Vehicles": 28,
    "Entertainment: Comics": 29,
    "Science: Gadgets": 30,
    "Entertainment: Japanese Anime & Manga": 31,
    "Entertainment: Cartoon & Animations": 32,
}

# Accord explicite obtenu sur les textes présentés pour l’arbitrage final.
CORRECTIONS_VALIDEES = {
    "S00646-q": "Which role is Bela Lugosi best known for playing in a 1931 horror film?",
    "S01104-q": "How many sharps are in the key signature of G-sharp minor?",
    "S02234-q": "Which group lists the four playable characters in the original Left 4 Dead?",
    "S02686-q": "Which of these pairs contains two Valve games set in the same universe?",
    "S03037-q": "What is a common name for medial tibial stress syndrome (MTSS)?",
    "S03139-c": "H2O",
    "S03184-c": "Cascading Style Sheets",
    "S04170-q": "The French Kingdom helped the United States gain their independence from "
    "Great Britain during the Revolutionary War.",
}

# Textes soumis à l’arbitrage final, conservés pour la traçabilité uniquement.
PROPOSITIONS_NON_RETENUES = {
    "S01813-q": "Which of these musical acts is not represented by a playable character in DJ Hero (2009)?",
    "S03390-q": "If a sheet of paper 0.10 mm thick doubled in thickness with each fold, "
    "after 50 folds it would be about three quarters of the mean Earth–Sun distance.",
    "S03725-q": "Which city had the world's busiest airport by total passenger traffic in 2025?",
    "S04010-q": "What is the Asian part of modern-day Turkey called?",
    "S04211-q": "Which Philippine national hero inspired the Philippine Revolution against Spanish colonial rule?",
    "S04763-q": "Which of these is a historical English common name for the Ethiopian wolf?",
    "S04763-c": "Simien Jackal",
    "S05004-q": "Which of these foods is one of Super Sonico's favorites?",
    "S05004-c": "Macarons",
    "S05155-q": 'Which studio animated the first season of "Log Horizon"?',
    "S05155-c": "Satelight",
    "S05197-i3": "I am lost, please show me the way.",
}

LIMITES_BENCHMARK = {
    117: "Difficulté des donjons sans version ni critère de classement explicites.",
    1813: "Le rôle jouable et le nombre d’avatars peuvent être interprétés différemment pour un duo.",
    1964: "Le vrai/faux peut porter sur l’existence d’une légende ou celle de la borne Polybius.",
    2150: "Le libellé ne distingue pas la provenance du sprite de l’origine du mème.",
    2962: "Corriger le distracteur Vulpes Vulpie le rendrait équivalent à Vulpes Vulpes.",
    3159: "Le choix False est conservé avec Cartillary Action. Corriger le terme changerait la vérité.",
    3390: "Le vrai/faux sur le papier plié omet l’épaisseur initiale, qui détermine le résultat.",
    3725: "La ville de l’aéroport le plus fréquenté dépend de l’année et de la métrique.",
    3871: "Le libellé confond la longueur du lieu et celle de son nom. Le record demande un périmètre.",
    4010: "Le libellé vise toute la Turquie, alors que la réponse désigne sa partie asiatique.",
    4211: "Le libellé attribue à José Rizal à la fois l’inspiration et la direction de la révolution.",
    4287: "Five times more than peut désigner un rapport de cinq ou de six. Les effectifs ne sont pas précisés.",
    4763: "Le libellé ne précise pas qu’un nom commun historique est attendu.",
    4815: "Le char le plus redouté n’est associé à aucun critère vérifiable.",
    5004: "Macroons reste ambigu entre macarons et macaroons dans la bonne réponse.",
    5155: "Le libellé confond les crédits d’animation et de production et ne précise pas la saison.",
    5197: "Deux choix de traduction sont quasi équivalents alors que le score en retient un seul.",
}

# Pour chaque libellé, la colonne qui distingue les variantes et ses deux valeurs.
# Les valeurs sont transcrites telles qu'elles apparaissent en Bronze.
ARBITRAGES = {
    "The &ldquo;fairy&rdquo; type made it&rsquo;s debut in which generation "
    "of the Pokemon core series games?": (
        "category", "General Knowledge", "Entertainment: Video Games",
    ),
    "How many sides does a heptagon have?": (
        "incorrect_answers", '["5", "4", "9"]', '["8", "6", "5"]',
    ),
    "When did the French Revolution begin?": (
        "correct_answer", "May 05 1789", "1789",
    ),
    "Who painted the Mona Lisa?": (
        "incorrect_answers",
        '["Pablo Picasso", "Claude Monet", "Vincent van Gogh"]',
        '["Pablo Picasso", " Vincent van Gogh", "Michelangelo"]',
    ),
}


def dedoublonner(questions):
    variantes = questions[questions["question"].duplicated(keep=False)]
    indices_a_ecarter = []

    for question, paire in variantes.groupby("question", sort=False):
        if question not in ARBITRAGES:
            raise ValueError(f"Question répétée sans arbitrage validé : {question}")

        colonne, a_ecarter, a_garder = ARBITRAGES[question]
        valeurs = paire[colonne]
        if len(paire) != 2 or set(valeurs) != {a_ecarter, a_garder}:
            raise ValueError(f"Variantes différentes de l'arbitrage validé : {question}")

        indices_a_ecarter.extend(paire.index[valeurs == a_ecarter])

    return questions.drop(index=indices_a_ecarter)


def ecrire_parquet(questions, destination):
    with TemporaryDirectory(dir=destination.parent) as dossier:
        fichier_temporaire = Path(dossier) / destination.name
        duckdb.from_df(questions).write_parquet(str(fichier_temporaire))
        fichier_temporaire.replace(destination)


def convertir_bronze():
    questions = pd.read_csv(BRONZE, encoding="utf-8-sig", dtype=str, keep_default_na=False)
    ecrire_parquet(questions, AVANT_DEDOUBLONNAGE)
    print(f"Conversion : {len(questions)} questions dans {AVANT_DEDOUBLONNAGE.relative_to(RACINE)}.")


def dedoublonner_parquet():
    if not AVANT_DEDOUBLONNAGE.is_file():
        raise FileNotFoundError("Parquet source absent. Exécuter d’abord « python preparer_silver.py convertir ».")

    questions = duckdb.read_parquet(str(AVANT_DEDOUBLONNAGE)).df()
    questions_silver = dedoublonner(questions)
    ecrire_parquet(questions_silver, QUESTIONS_DEDOUBLONNEES)
    nb_ecartees = len(questions) - len(questions_silver)
    print(f"Variantes écartées : {nb_ecartees}.")
    print(f"Après dédoublonnage : {len(questions_silver)} questions dans "
          f"{QUESTIONS_DEDOUBLONNEES.relative_to(RACINE)}.")


def normaliser_texte(texte):
    if not isinstance(texte, str):
        raise ValueError("Chaque champ de texte doit contenir une chaîne.")
    texte = normalize("NFC", unescape(texte)).strip()
    if not texte:
        raise ValueError("Un champ de texte est vide après normalisation.")
    return texte


def parser_reponses_incorrectes(valeur, libelle):
    try:
        reponses = json.loads(valeur)
    except (TypeError, ValueError) as erreur:
        raise ValueError(f"Réponses incorrectes illisibles pour {libelle!r}.") from erreur
    if not isinstance(reponses, list):
        raise ValueError(f"Liste de réponses incorrectes attendue pour {libelle!r}.")
    return reponses


def normaliser_questions(questions):
    if questions.empty:
        raise ValueError("Le Parquet Silver ne contient aucune question.")

    def nettoyer(texte):
        return re.sub(r" {2,}", " ", normaliser_texte(texte))

    resultat = questions.copy()
    for colonne in COLONNES_TEXTE:
        resultat[colonne] = questions[colonne].map(nettoyer)
    resultat["incorrect_answers"] = [
        [nettoyer(reponse) for reponse in parser_reponses_incorrectes(valeur, libelle)]
        for valeur, libelle in zip(questions["incorrect_answers"], questions["question"], strict=True)
    ]
    return resultat


def normaliser_parquet():
    if not QUESTIONS_DEDOUBLONNEES.is_file():
        raise FileNotFoundError(f"Jalon Silver dédoublonné introuvable : {QUESTIONS_DEDOUBLONNEES}")

    questions = duckdb.read_parquet(str(QUESTIONS_DEDOUBLONNEES)).df()
    resultat = normaliser_questions(questions)
    ecrire_parquet(resultat, QUESTIONS_NORMALISEES)
    print(f"Normalisation : {len(resultat)} questions dans {QUESTIONS_NORMALISEES.relative_to(RACINE)}.")


def empreinte(*valeurs):
    contenu = json.dumps(valeurs, ensure_ascii=False, separators=(",", ":"))
    return sha256(contenu.encode("utf-8")).hexdigest()


def identifier_et_ordonner(champs, distracteurs):
    identifiant = empreinte(*(champs[colonne] for colonne in COLONNES_TEXTE), sorted(distracteurs))
    choix = sorted(
        [champs["correct_answer"], *distracteurs],
        key=lambda reponse: (empreinte("choix", SEED_PILOTE, identifiant, reponse), reponse),
    )
    return identifiant, choix


def preparer_questions(questions):
    if questions.empty:
        raise ValueError("Le Parquet Silver ne contient aucune question.")

    enregistrements = []
    colonnes = [*COLONNES_TEXTE, "incorrect_answers"]
    for ligne in questions[colonnes].itertuples(index=False, name=None):
        champs = dict(zip(COLONNES_TEXTE, map(normaliser_texte, ligne[:-1])))
        libelle = champs["question"]
        reponses_brutes = parser_reponses_incorrectes(ligne[-1], libelle)
        distracteurs = [normaliser_texte(reponse) for reponse in reponses_brutes]
        bonne_reponse = champs["correct_answer"]
        choix = [bonne_reponse, *distracteurs]
        type_question = champs["type"]
        if len(choix) != NOMBRE_CHOIX.get(type_question) or len(set(choix)) != len(choix):
            raise ValueError(f"Nombre ou unicité des choix non conforme pour {libelle!r}.")
        if type_question == "boolean" and set(choix) != {"True", "False"}:
            raise ValueError(f"Choix True et False attendus pour {libelle!r}.")
        if champs["difficulty"] not in {"easy", "medium", "hard"}:
            raise ValueError(f"Difficulté inconnue pour {libelle!r}.")

        question_id, choix = identifier_et_ordonner(champs, distracteurs)
        enregistrements.append({
            "question_id": question_id,
            **champs,
            "incorrect_answers": distracteurs,
            "choices": choix,
            "correct_choice": ascii_uppercase[choix.index(bonne_reponse)],
        })

    resultat = pd.DataFrame.from_records(enregistrements)
    if not resultat["question_id"].is_unique or not resultat["question"].str.casefold().is_unique:
        raise ValueError("Les identifiants et les libellés normalisés doivent être uniques.")
    return resultat.sort_values("question_id", ignore_index=True)


def empreinte_fichier(chemin):
    return sha256(chemin.read_bytes()).hexdigest()


def lire_parquet(chemin, schema):
    relation = duckdb.read_parquet(str(chemin))
    schema_reel = tuple(zip(relation.columns, map(str, relation.types), strict=True))
    if schema_reel != schema:
        raise ValueError(f"Schéma inattendu dans {chemin.name} : {schema_reel}.")
    return [dict(zip(relation.columns, ligne, strict=True)) for ligne in relation.fetchall()]


def cle_comparaison_libelle(libelle):
    texte = normalize("NFC", libelle.casefold())
    return "".join(
        caractere for caractere in texte
        if not caractere.isspace() and not category(caractere).startswith("P")
        and caractere not in "`´ʻʼ"
    )


def doublons_libelles(questions):
    groupes = defaultdict(list)
    for ligne in questions:
        groupes[cle_comparaison_libelle(ligne["question"])].append(ligne)
    return [groupe for groupe in groupes.values() if len(groupe) > 1]


def afficher_doublons_libelles(questions):
    groupes = doublons_libelles(questions)
    effectif = sum(map(len, groupes))
    print(f"Contrôle des libellés sans ponctuation, guillemets, casse ni espaces : "
          f"{len(groupes)} groupes, {effectif} questions signalées.")
    for rang, groupe in enumerate(groupes, start=1):
        for ligne in groupe:
            print(f"  {rang}. {ligne['question_id']} — {ligne['question']}")


def verifier_questions(questions, nombre_attendu=NOMBRE_QUESTIONS):
    if len(questions) != nombre_attendu:
        raise ValueError(f"{nombre_attendu} questions attendues, {len(questions)} lues.")
    for rang, ligne in enumerate(questions, start=1):
        distracteurs = ligne["incorrect_answers"]
        if not isinstance(distracteurs, list):
            raise ValueError(f"Rang {rang} : liste de distracteurs attendue.")
        textes = [*(ligne[colonne] for colonne in COLONNES_TEXTE), *distracteurs]
        if any(not isinstance(texte, str) or not texte.strip() for texte in textes):
            raise ValueError(f"Rang {rang} : texte nul, vide ou de type inattendu.")
        if ligne["difficulty"] not in {"easy", "medium", "hard"}:
            raise ValueError(f"Rang {rang} : difficulté inconnue.")
        choix = [ligne["correct_answer"], *distracteurs]
        if len(choix) != NOMBRE_CHOIX.get(ligne["type"]) or len(set(choix)) != len(choix):
            raise ValueError(f"Rang {rang} : type, nombre ou unicité des choix non conforme.")
        if ligne["type"] == "boolean" and set(choix) != {"True", "False"}:
            raise ValueError(f"Rang {rang} : choix True et False attendus.")

    if {ligne["category"] for ligne in questions} != CATEGORIES_OPENTDB.keys():
        raise ValueError("Le catalogue OpenTDB et les catégories Silver diffèrent.")
    if len(set(CATEGORIES_OPENTDB.values())) != len(CATEGORIES_OPENTDB):
        raise ValueError("Plusieurs catégories partagent le même identifiant OpenTDB.")

    lignes_strictes = Counter(
        (*(ligne[colonne] for colonne in COLONNES_TEXTE), tuple(ligne["incorrect_answers"]))
        for ligne in questions
    )
    libelles = Counter(ligne["question"] for ligne in questions)
    plis_casse = Counter(ligne["question"].casefold() for ligne in questions)
    repetitions = [
        [valeur for valeur, total in comptage.items() if total > 1]
        for comptage in (lignes_strictes, libelles, plis_casse)
    ]
    if any(repetitions):
        raise ValueError(
            "Doublons stricts, libellés répétés exacts ou libellés répétés sans la casse : "
            f"{repetitions}"
        )


def lire_classement():
    with CLASSEMENT.open(encoding="utf-8-sig", newline="") as fichier:
        lecteur = csv.DictReader(fichier, delimiter=";")
        classement = list(lecteur)
    effectifs = Counter(entree["statut"] for entree in classement)
    if effectifs != {"Proposée": 1019, "À éclaircir": 11}:
        raise ValueError(f"Effectifs inattendus dans le classement : {effectifs}.")
    return classement


def valeur_champ(ligne, champ):
    if champ in {"question", "correct_answer"}:
        return ligne[champ]
    position = re.fullmatch(r"incorrect_answers\[([123])\]", champ)
    if position is None:
        raise ValueError(f"Champ de question inconnu dans le rapport : {champ}.")
    indice = int(position[1])
    return ligne["incorrect_answers"][indice - 1]


def appliquer_corrections(source, classement):
    questions = [ligne.copy() for ligne in source]
    positions = {}
    ids_vus = set()
    for entree in classement:
        identifiant = entree["id_proposition"]
        rang = int(entree["rang_silver"])
        champ = entree["champ"]
        if identifiant in ids_vus or not 1 <= rang <= len(source):
            raise ValueError(f"Référence Silver inattendue : {identifiant}.")
        ligne = source[rang - 1]
        ids_vus.add(identifiant)
        if entree["sha256_silver_source"] != EMPREINTE_NORMALISEES:
            raise ValueError(f"Jalon du rapport inattendu : {identifiant}.")
        if valeur_champ(ligne, champ) != entree["texte_original"]:
            raise ValueError(f"Le texte original ne concorde pas : {identifiant}.")
        if identifiant in CORRECTIONS_VALIDEES:
            attendu = {"q": "question", "c": "correct_answer"}[identifiant[-1]]
            texte_valide = CORRECTIONS_VALIDEES[identifiant]
            if identifiant != f"S{rang:05d}-{identifiant[-1]}" or champ != attendu:
                raise ValueError(f"Le rang ou le champ validé diffère : {identifiant}.")
            if texte_valide == entree["texte_original"] or (rang, champ) in positions:
                raise ValueError(f"Correction redondante : {identifiant}.")
            questions[rang - 1][champ] = texte_valide
            positions[rang, champ] = texte_valide
    manquants = CORRECTIONS_VALIDEES.keys() - ids_vus
    if manquants:
        raise ValueError(f"Corrections validées absentes du classement : {sorted(manquants)}.")
    return questions, positions


def enrichir_ligne(ligne):
    identifiant, choix = identifier_et_ordonner(ligne, ligne["incorrect_answers"])
    correcte = ligne["correct_answer"]
    attendue = correcte if ligne["type"] == "boolean" else ascii_uppercase[choix.index(correcte)]
    return {
        **ligne,
        "question_id": identifiant,
        "answer_choices": choix,
        "expected_answer": attendue,
        "category_id": CATEGORIES_OPENTDB[ligne["category"]],
    }


def verifier_finalisation(source, final, corrections):
    verifier_questions(final)
    differences = {}
    identifiants = set()
    for rang, (avant, apres) in enumerate(zip(source, final, strict=True), start=1):
        for champ in COLONNES_SOURCE:
            if avant[champ] != apres[champ]:
                differences[rang, champ] = apres[champ]
        identifiant = apres["question_id"]
        if not re.fullmatch(r"[0-9a-f]{64}", identifiant) or identifiant in identifiants:
            raise ValueError(f"Rang {rang} : question_id mal formé ou répété.")
        identifiants.add(identifiant)
        choix = apres["answer_choices"]
        bonne = apres["correct_answer"]
        attendue = apres["expected_answer"]
        if Counter(choix) != Counter([bonne, *apres["incorrect_answers"]]) or choix.count(bonne) != 1:
            raise ValueError(f"Rang {rang} : choix incohérents ou bonne réponse non unique.")
        if apres["type"] == "boolean":
            valide = attendue in {"True", "False"} and attendue == bonne
        else:
            valide = attendue in {"A", "B", "C", "D"} and choix[ascii_uppercase.index(attendue)] == bonne
        if not valide:
            raise ValueError(f"Rang {rang} : expected_answer incohérent.")
        if apres["category_id"] != CATEGORIES_OPENTDB[apres["category"]]:
            raise ValueError(f"Rang {rang} : category_id incohérent.")

    if differences != corrections:
        raise ValueError("Les changements dans les six champs source diffèrent des corrections validées.")

    # Permuter simultanément l’ordre des lignes et celui des distracteurs de chaque ligne.
    for ligne in reversed(final):
        permutee = {champ: ligne[champ] for champ in COLONNES_SOURCE}
        permutee["incorrect_answers"] = list(reversed(permutee["incorrect_answers"]))
        recalculee = enrichir_ligne(permutee)
        for champ in ("question_id", "answer_choices", "expected_answer"):
            if recalculee[champ] != ligne[champ]:
                raise ValueError(f"Reproductibilité en échec pour {ligne['question_id']} ({champ}).")


def appliquer_arbitrages_doublons(questions):
    par_id = {ligne["question_id"]: ligne for ligne in questions}
    decisions = {}
    for groupe, (garder, exclure, motif) in enumerate(ARBITRAGES_DOUBLONS_SILVER, start=1):
        for decision, (question_id, libelle) in (("GARDER", garder), ("EXCLURE", exclure)):
            if question_id not in par_id or par_id[question_id]["question"] != libelle or question_id in decisions:
                raise ValueError(f"Groupe {groupe} : identifiant ou libellé incohérent pour {question_id}.")
            decisions[question_id] = (groupe, decision, motif)
        if cle_comparaison_libelle(garder[1]) != cle_comparaison_libelle(exclure[1]):
            raise ValueError(f"Groupe {groupe} : les clés de comparaison diffèrent.")
    exclus = {question_id for question_id, (_, decision, _) in decisions.items() if decision == "EXCLURE"}
    conservees = [ligne for ligne in questions if ligne["question_id"] not in exclus]
    verifier_questions(conservees, NOMBRE_QUESTIONS_FINAL)
    return conservees, decisions


def ecrire_rapport_qualite(chemin, classement, source, enrichies, arbitrages):
    entrees = list(classement)
    par_rang = {int(entree["rang_silver"]): entree for entree in classement}
    nouveaux_ids = PROPOSITIONS_NON_RETENUES.keys() - {entree["id_proposition"] for entree in entrees}
    for identifiant in sorted(nouveaux_ids):
        rang = int(identifiant[1:6])
        champ = "question" if identifiant.endswith("-q") else f"incorrect_answers[{identifiant[-1]}]"
        entete = par_rang[rang]
        entrees.append({
            **{cle: "" for cle in entete},
            "id_proposition": identifiant,
            "statut": "Soumise à l’arbitrage final",
            "role_champ": "Question" if champ == "question" else "Mauvaise réponse",
            "rang_silver": str(rang),
            "ligne_bronze": entete["ligne_bronze"],
            "champ": champ,
            "texte_original": valeur_champ(source[rang - 1], champ),
            "sha256_silver_source": EMPREINTE_NORMALISEES,
            **{cle: valeur for cle, valeur in entete.items() if cle.endswith("_contexte")},
        })

    rapport = []
    for entree in entrees:
        identifiant = entree["id_proposition"]
        rang = int(entree["rang_silver"])
        ancienne_valeur = entree["texte_original"]
        nouvelle_valeur = valeur_champ(enrichies[rang - 1], entree["champ"])
        if identifiant in CORRECTIONS_VALIDEES:
            decision = "Appliquée"
            texte_arbitre = CORRECTIONS_VALIDEES[identifiant]
        else:
            decision = "Laissée en l’état" if entree["statut"] == "À éclaircir" else "Non retenue"
            texte_arbitre = PROPOSITIONS_NON_RETENUES.get(identifiant, "")
        if (decision == "Appliquée") != (ancienne_valeur != nouvelle_valeur):
            raise ValueError(f"Traçabilité incohérente pour {identifiant}.")
        limite = LIMITES_BENCHMARK.get(rang, "")
        if decision == "Laissée en l’état" and not limite:
            limite = entree["justification"]
        rapport.append({
            **entree,
            "decision_finale": decision,
            "proposition_arbitrage": texte_arbitre,
            "texte_avant": ancienne_valeur,
            "texte_apres": nouvelle_valeur,
            "limite_benchmark": limite,
            "question_id": enrichies[rang - 1]["question_id"],
        })

    for rang, ligne in enumerate(enrichies, start=1):
        question_id = ligne["question_id"]
        if question_id not in arbitrages:
            continue
        groupe, decision, motif = arbitrages[question_id]
        rapport.append({
            **dict.fromkeys(rapport[0], ""),
            "id_proposition": f"D{groupe:02d}-{decision}",
            "statut": "Arbitrage de doublon validé",
            "categorie_validation": "Doublon de libellé",
            "groupe_validation": str(groupe),
            "role_champ": "Question",
            "rang_silver": str(rang),
            "champ": "question",
            "type": ligne["type"],
            "justification": motif,
            "sha256_silver_source": EMPREINTE_SILVER_INITIAL,
            "question_contexte": ligne["question"],
            "bonne_reponse_contexte": ligne["correct_answer"],
            "texte_original": ligne["question"],
            "decision_finale": decision,
            "texte_avant": ligne["question"],
            "texte_apres": ligne["question"] if decision == "GARDER" else "",
            "question_id": question_id,
        })

    rapport.sort(key=lambda entree: entree["id_proposition"])
    with chemin.open("w", encoding="utf-8-sig", newline="") as fichier:
        writer = csv.DictWriter(fichier, fieldnames=list(rapport[0]), delimiter=";")
        writer.writeheader()
        writer.writerows(rapport)
    with chemin.open(encoding="utf-8-sig", newline="") as fichier:
        if list(csv.DictReader(fichier, delimiter=";")) != rapport:
            raise ValueError("Le rapport qualité relu diffère du rapport écrit.")
    return Counter(entree["decision_finale"] for entree in rapport)


def finaliser_silver():
    fichiers_proteges = [
        fichier for dossier in (BRONZE.parent, SILVER.parent)
        for fichier in dossier.iterdir() if fichier.is_file()
    ]
    empreintes_avant = {chemin: empreinte_fichier(chemin) for chemin in fichiers_proteges}
    for fichier, attendu in (
        (BRONZE, EMPREINTE_BRONZE), (QUESTIONS_NORMALISEES, EMPREINTE_NORMALISEES),
        (CLASSEMENT, EMPREINTE_CLASSEMENT),
    ):
        if empreintes_avant.get(fichier) != attendu:
            raise ValueError(f"Fichier manquant ou différent du jalon : {fichier.name}.")

    source = lire_parquet(QUESTIONS_NORMALISEES, SCHEMA_SOURCE)
    verifier_questions(source)
    classement = lire_classement()
    questions, corrections = appliquer_corrections(source, classement)
    enrichies = [enrichir_ligne(ligne) for ligne in questions]
    verifier_finalisation(source, enrichies, corrections)
    final, arbitrages = appliquer_arbitrages_doublons(enrichies)
    donnees = pd.DataFrame.from_records(final).astype({"category_id": "int32"})

    with TemporaryDirectory(dir=SILVER.parent) as temporaire:
        dossier = Path(temporaire) / CANDIDAT.name
        dossier.mkdir()
        parquet = dossier / SILVER.name
        rapport = dossier / RAPPORT_QUALITE
        ecrire_parquet(donnees, parquet)
        relu = lire_parquet(parquet, SCHEMA_FINAL)
        if relu != final:
            raise ValueError("Le Parquet relu diffère des enregistrements enrichis.")
        decisions = ecrire_rapport_qualite(rapport, classement, source, enrichies, arbitrages)
        for chemin, attendu in empreintes_avant.items():
            if empreinte_fichier(chemin) != attendu:
                raise ValueError(f"Fichier protégé modifié pendant l’exécution : {chemin.name}.")
        try:
            dossier.rename(CANDIDAT)
        except OSError:
            if not CANDIDAT.is_dir():
                raise
            if (
                lire_parquet(CANDIDAT / SILVER.name, SCHEMA_FINAL) != relu
                or (CANDIDAT / RAPPORT_QUALITE).read_bytes() != rapport.read_bytes()
            ):
                raise FileExistsError(f"Un candidat différent existe déjà : {CANDIDAT}.") from None
            print("Le candidat et le rapport existants reproduisent les résultats.")

    total_types = Counter(ligne["type"] for ligne in relu)
    total_categories = len({ligne["category"] for ligne in relu})
    print(f"Candidat : {len(relu)} × {len(SCHEMA_FINAL)}, {total_types['multiple']} QCM, "
          f"{total_types['boolean']} vrai/faux et {total_categories} catégories.")
    print(f"Arbitrage : {len(corrections)} corrections historiques et {len(enrichies) - len(relu)} exclusions validées. "
          f"Rapport : {dict(decisions)}.")
    print("Contrôles source et candidat : valeurs et types conformes, 0 doublon strict, "
          "0 libellé répété avec ou sans distinction de casse.")
    print("Avant exclusions :")
    afficher_doublons_libelles(enrichies)
    print("Après exclusions :")
    afficher_doublons_libelles(relu)
    print("Relecture : schéma et valeurs identiques, identifiants uniques, "
          "4/2 choix et réponses attendues cohérents. Reproductibilité vérifiée après permutation.")
    print("Les six champs source sont conservés hors arbitrage. Empreintes Bronze et Silver contrôlées.")
    print(f"Fichiers : {CANDIDAT.relative_to(RACINE)}/")


def selectionner_pilote(questions):
    taille_source = len(questions)
    taille_pilote = max(1, (taille_source + 5) // 10)
    lignes = list(questions[[*COLONNES_STRATES, "question_id"]].itertuples(index=False, name=None))
    effectifs = Counter(ligne[:-1] for ligne in lignes)
    quotas = {strate: effectif * taille_pilote // taille_source for strate, effectif in effectifs.items()}
    restes = {strate: effectif * taille_pilote % taille_source for strate, effectif in effectifs.items()}
    ordre_restes = sorted(restes, key=lambda strate: (-restes[strate], strate))
    places_a_distribuer = taille_pilote - sum(quotas.values())
    for strate in ordre_restes[:places_a_distribuer]:
        quotas[strate] += 1

    ordre_pilote = sorted(lignes, key=lambda ligne: empreinte("pilote", SEED_PILOTE, ligne[-1]))
    identifiants = []
    for *dimensions, question_id in ordre_pilote:
        strate = tuple(dimensions)
        if quotas[strate] > 0:
            identifiants.append(question_id)
            quotas[strate] -= 1

    return pd.DataFrame({
        "pilot_order": range(1, taille_pilote + 1),
        "question_id": identifiants,
        "seed": SEED_PILOTE,
    })


def preparer_pilote():
    if not QUESTIONS_DEDOUBLONNEES.is_file():
        raise FileNotFoundError("Silver dédoublonné absent. Exécuter d’abord « python preparer_silver.py tout ».")

    source = duckdb.read_parquet(str(QUESTIONS_DEDOUBLONNEES)).df()
    questions = preparer_questions(source)
    manifeste = selectionner_pilote(questions)
    ecrire_parquet(questions, QUESTIONS_BENCHMARK)
    ecrire_parquet(manifeste, MANIFESTE_PILOTE)
    print(f"Benchmark : {len(questions)} questions dans {QUESTIONS_BENCHMARK.relative_to(RACINE)}.")
    print(f"Pilote : {len(manifeste)} questions dans {MANIFESTE_PILOTE.relative_to(RACINE)} (seed {SEED_PILOTE}).")


def main():
    parser = ArgumentParser(description="Préparer les questions Silver et l’échantillon du pilote.")
    parser.add_argument(
        "etape", nargs="?",
        choices=("convertir", "dedoublonner", "normaliser", "finaliser", "controler-doublons", "pilote", "tout"),
        default="tout", help="finaliser produit le candidat Silver et son rapport qualité",
    )
    args = parser.parse_args()

    if args.etape in ("convertir", "tout"):
        convertir_bronze()
    if args.etape in ("dedoublonner", "tout"):
        dedoublonner_parquet()
    if args.etape == "normaliser":
        normaliser_parquet()
    if args.etape == "finaliser":
        finaliser_silver()
    if args.etape == "controler-doublons":
        afficher_doublons_libelles(lire_parquet(SILVER, SCHEMA_FINAL))
    if args.etape == "pilote":
        preparer_pilote()


if __name__ == "__main__":
    main()
