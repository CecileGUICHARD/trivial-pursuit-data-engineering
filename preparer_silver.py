from argparse import ArgumentParser
from collections import Counter
from hashlib import sha256
from html import unescape
import json
from pathlib import Path
import re
from string import ascii_uppercase
from tempfile import TemporaryDirectory
from unicodedata import normalize

import duckdb
import pandas as pd


RACINE = Path(__file__).resolve().parent
BRONZE = RACINE / "data" / "bronze" / "questions_raw.csv"
SILVER = RACINE / "data" / "silver" / "questions_clean.parquet"
AVANT_DEDOUBLONNAGE = SILVER.with_name("questions_avant_dedoublonnage.parquet")
QUESTIONS_NORMALISEES = SILVER.with_name("questions_normalisees.parquet")
QUESTIONS_BENCHMARK = SILVER.with_name("questions_benchmark.parquet")
MANIFESTE_PILOTE = SILVER.with_name("pilot_question_ids.parquet")
SEED_PILOTE = 42
COLONNES_STRATES = ("category", "difficulty", "type")
COLONNES_TEXTE = (*COLONNES_STRATES, "question", "correct_answer")
NOMBRE_CHOIX = {"boolean": 2, "multiple": 4}

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
    ecrire_parquet(questions_silver, SILVER)
    nb_ecartees = len(questions) - len(questions_silver)
    print(f"Variantes écartées : {nb_ecartees}.")
    print(f"Après dédoublonnage : {len(questions_silver)} questions dans {SILVER.relative_to(RACINE)}.")


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
    if not SILVER.is_file():
        raise FileNotFoundError(f"Jalon Silver dédoublonné introuvable : {SILVER}")

    questions = duckdb.read_parquet(str(SILVER)).df()
    resultat = normaliser_questions(questions)
    ecrire_parquet(resultat, QUESTIONS_NORMALISEES)
    print(f"Normalisation : {len(resultat)} questions dans {QUESTIONS_NORMALISEES.relative_to(RACINE)}.")


def empreinte(*valeurs):
    contenu = json.dumps(valeurs, ensure_ascii=False, separators=(",", ":"))
    return sha256(contenu.encode("utf-8")).hexdigest()


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

        valeurs_identifiantes = [champs[colonne] for colonne in COLONNES_TEXTE]
        question_id = empreinte(*valeurs_identifiantes, sorted(distracteurs))
        choix.sort(key=lambda reponse: empreinte("choix", SEED_PILOTE, question_id, reponse))
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
    if not SILVER.is_file():
        raise FileNotFoundError("Silver dédoublonné absent. Exécuter d’abord « python preparer_silver.py tout ».")

    source = duckdb.read_parquet(str(SILVER)).df()
    questions = preparer_questions(source)
    manifeste = selectionner_pilote(questions)
    ecrire_parquet(questions, QUESTIONS_BENCHMARK)
    ecrire_parquet(manifeste, MANIFESTE_PILOTE)
    print(f"Benchmark : {len(questions)} questions dans {QUESTIONS_BENCHMARK.relative_to(RACINE)}.")
    print(f"Pilote : {len(manifeste)} questions dans {MANIFESTE_PILOTE.relative_to(RACINE)} (seed {SEED_PILOTE}).")


def main():
    parser = ArgumentParser(description="Préparer les questions Silver et l’échantillon du pilote.")
    parser.add_argument(
        "etape", nargs="?", choices=("convertir", "dedoublonner", "normaliser", "pilote", "tout"), default="tout",
        help="tout enchaîne la conversion et le dédoublonnage, normaliser prépare le Parquet de validation",
    )
    args = parser.parse_args()

    if args.etape in ("convertir", "tout"):
        convertir_bronze()
    if args.etape in ("dedoublonner", "tout"):
        dedoublonner_parquet()
    if args.etape == "normaliser":
        normaliser_parquet()
    if args.etape == "pilote":
        preparer_pilote()


if __name__ == "__main__":
    main()
