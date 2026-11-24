from argparse import ArgumentParser
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from itertools import combinations
import json
import os
from pathlib import Path
from statistics import mean, median
from subprocess import SubprocessError, TimeoutExpired, check_output, run
from tempfile import TemporaryDirectory
from time import perf_counter
from urllib.parse import urlsplit
from uuid import uuid4

import duckdb
import pandas as pd

from preparer_silver import (
    BRONZE, COLONNES_STRATES, EMPREINTE_SILVER_INITIAL, NOMBRE_QUESTIONS, NOMBRE_QUESTIONS_FINAL,
    RACINE, SCHEMA_FINAL, SEED_PILOTE, SILVER, empreinte,
    empreinte_fichier, ecrire_parquet, lire_parquet, selectionner_pilote, verifier_questions,
)


EMPREINTE_SILVER = "af2e683573b68effb0832fff695e3acfeb138e3a67449ebd306814a00f67a92e"
EMPREINTE_MANIFESTE_INITIAL = "f130cda8a5ca4c21c2a40016d3154d3f37bcb9de9c94446814afc460687305e5"
DOSSIER_PILOTE = SILVER.parent / "pilot_lot2"
MANIFESTE = DOSSIER_PILOTE / "pilot_question_ids.parquet"
METADONNEES = DOSSIER_PILOTE / "manifest_metadata.json"
JOURNAL = DOSSIER_PILOTE / "pilot.duckdb"
SCHEMA_MANIFESTE = (("pilot_order", "BIGINT"), ("question_id", "VARCHAR"), ("seed", "BIGINT"))
PROMPTS_HISTORIQUES = ("P1_choices", "P2_expert")
PROMPT_P3 = "P3_expert_advanced"
FICHIERS_RESULTATS = {
    "P1_choices": SILVER.parent / "gemma_p1_choices.parquet",
    "P2_expert": SILVER.parent / "gemma_p2_expert.parquet",
    PROMPT_P3: SILVER.parent / "gemma_p3_expert_advanced.parquet",
}


@dataclass(frozen=True)
class StockageInference:
    journal: Path
    bronze: Path
    silver: Path


STOCKAGE_PILOTE = StockageInference(JOURNAL, BRONZE.parent, SILVER.parent)
STOCKAGE_P3 = StockageInference(DOSSIER_PILOTE / "pilot_p3.duckdb", BRONZE.parent, SILVER.parent)
SCHEMA_BRONZE = (
    ("question_id", "VARCHAR"), ("model_id", "VARCHAR"), ("prompt_id", "VARCHAR"),
    ("inference_id", "UUID"), ("pilot_order", "INTEGER"), ("segment_id", "UUID"),
    ("raw_response", "VARCHAR"), ("response_time", "DOUBLE"), ("status", "VARCHAR"),
    ("configuration", "VARCHAR"), ("error_type", "VARCHAR"), ("error_message", "VARCHAR"),
)
CONSIGNE = "Answer the following general knowledge question."
CONSIGNES_FORMAT = {
    "multiple": "Reply with only one uppercase letter: A, B, C, or D.",
    "boolean": "Reply with only True or False.",
}
REPONSES_ADMISES = {"multiple": tuple("ABCD"), "boolean": ("True", "False")}
ROLE_EXPERT = "You are a general knowledge expert."
CONSIGNES_P3 = {
    "multiple": (
        "Carefully analyze the question and evaluate each answer choice.\n"
        "Use your factual knowledge to eliminate incorrect options.\n"
        "Check your answer before responding."
    ),
    "boolean": (
        "Carefully evaluate the statement using your factual knowledge.\n"
        "Check its accuracy before responding."
    ),
}
PARAMETRES = {
    "temperature": 0, "top_k": 1, "top_p": 1, "min_p": 0, "repeat_penalty": 1,
    "max_output_tokens": 16, "context_length": 4096, "reasoning": "off",
    "stream": False, "store": False,
}
DELAI = 60
INTERVALLE_EXPORT = 25
QUESTION_ECHAUFFEMENT = {
    "type": "multiple", "question": "Which option is the letter Z?",
    "answer_choices": ["Alpha", "Beta", "Z", "Delta"],
}


def json_compact(objet):
    return json.dumps(objet, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def charger_silver():
    if empreinte_fichier(SILVER) != EMPREINTE_SILVER:
        raise ValueError("L’empreinte du Silver diffère du corpus révisé attendu.")
    questions = lire_parquet(SILVER, SCHEMA_FINAL)
    if empreinte_fichier(SILVER) != EMPREINTE_SILVER:
        raise ValueError("Le Silver a changé pendant la lecture.")
    verifier_questions(questions, NOMBRE_QUESTIONS_FINAL)
    if len({question["question_id"] for question in questions}) != len(questions):
        raise ValueError("Les identifiants Silver ne sont pas uniques.")
    return questions


def preparer_manifeste():
    questions = charger_silver()
    if DOSSIER_PILOTE.exists():
        return charger_manifeste(questions)

    selection = selectionner_pilote(pd.DataFrame.from_records(questions))
    with TemporaryDirectory(dir=SILVER.parent) as temporaire:
        dossier = Path(temporaire) / DOSSIER_PILOTE.name
        dossier.mkdir()
        parquet = dossier / MANIFESTE.name
        ecrire_parquet(selection, parquet)
        if lire_parquet(parquet, SCHEMA_MANIFESTE) != selection.to_dict("records"):
            raise ValueError("Le nouveau manifeste diffère à la relecture.")
        meta = {
            "dataset": str(SILVER.relative_to(RACINE)), "dataset_sha256": EMPREINTE_SILVER,
            "population": len(questions), "sample_size": len(selection),
            "selection_dataset_sha256": EMPREINTE_SILVER, "selection_population": len(questions),
            "manifest_sha256": empreinte_fichier(parquet), "seed": SEED_PILOTE,
            "stratification": list(COLONNES_STRATES),
            "allocation": "10 %, arrondi demi supérieur, plus forts restes, départage lexicographique",
            "order": 'SHA-256 du JSON UTF-8 compact ["pilote",42,question_id]',
        }
        (dossier / METADONNEES.name).write_text(json_compact(meta) + "\n", encoding="utf-8")
        dossier.rename(DOSSIER_PILOTE)
    return charger_manifeste(questions)


def charger_manifeste(questions):
    meta = json.loads(METADONNEES.read_text(encoding="utf-8"))
    manifeste = lire_parquet(MANIFESTE, SCHEMA_MANIFESTE)
    if (meta["dataset_sha256"] != EMPREINTE_SILVER
            or meta["manifest_sha256"] != empreinte_fichier(MANIFESTE)
            or meta["population"] != len(questions)
            or meta["sample_size"] != len(manifeste)
            or meta["seed"] != SEED_PILOTE):
        raise ValueError("Les empreintes ou les métadonnées du manifeste diffèrent.")
    origine = meta["selection_dataset_sha256"]
    if origine == EMPREINTE_SILVER_INITIAL:
        if (meta["selection_population"] != NOMBRE_QUESTIONS
                or meta["manifest_sha256"] != EMPREINTE_MANIFESTE_INITIAL):
            raise ValueError("Le manifeste repris diffère du tirage initial validé.")
    elif origine == EMPREINTE_SILVER:
        attendue = selectionner_pilote(pd.DataFrame.from_records(questions)).to_dict("records")
        if meta["selection_population"] != len(questions) or manifeste != attendue:
            raise ValueError("Le manifeste diffère du tirage reproductible sur le Silver révisé.")
    else:
        raise ValueError("L’origine du tirage n’est pas reconnue.")
    par_identifiant = {question["question_id"]: question for question in questions}
    if any(ligne["question_id"] not in par_identifiant for ligne in manifeste):
        raise ValueError("Le manifeste référence des questions absentes du Silver révisé.")
    return [par_identifiant[ligne["question_id"]] for ligne in manifeste], meta


def construire_prompt(question, prompt_id):
    type_question = question["type"]
    choix = question["answer_choices"]
    if type_question == "multiple":
        choix = [f"{lettre}. {texte}" for lettre, texte in zip("ABCD", choix, strict=True)]
    texte = "\n\n".join((f"{CONSIGNE} {CONSIGNES_FORMAT[type_question]}", question["question"], "\n".join(choix)))
    if prompt_id == PROMPT_P3:
        return f"{ROLE_EXPERT}\n{CONSIGNES_P3[type_question]}\n{texte}"
    return f"{ROLE_EXPERT}\n{texte}" if prompt_id == "P2_expert" else texte


def score(raw_response, question):
    reponse = raw_response.strip()
    conforme = reponse in REPONSES_ADMISES[question["type"]]
    return reponse if conforme else None, conforme and reponse == question["expected_answer"], conforme


class ErreurAPI(Exception):
    def __init__(self, code, message, duree=None):
        super().__init__(message)
        self.code = code
        self.duree = duree


class LMStudio:
    def __init__(self, adresse, curl):
        url = urlsplit(adresse)
        if (url.scheme != "http" or url.hostname not in {"127.0.0.1", "localhost", "::1"}
                or url.username or url.password or url.path.rstrip("/") or url.query or url.fragment):
            raise ValueError("Utiliser une adresse HTTP locale de LM Studio.")
        self.adresse = adresse.rstrip("/")
        self.curl = curl
        self.token = os.environ.get("LM_STUDIO_API_TOKEN")

    def requete(self, chemin, donnees=None):
        options = []
        if self.token:
            options.append(f'header = {json.dumps(f"Authorization: Bearer {self.token}")}')
        if donnees is not None:
            options.append('header = "Content-Type: application/json"')
            options.append(f"data-binary = {json.dumps(json_compact(donnees), ensure_ascii=False)}")
        commande = [self.curl, "--disable", "--silent", "--show-error", "--noproxy", "*",
                    "--max-time", str(DELAI), "--write-out", "\n%{http_code} %{time_total}",
                    "--config", "-", f"{self.adresse}/api/v1/{chemin}"]
        debut = perf_counter()
        try:
            processus = run(commande, input=("\n".join(options) + "\n").encode("utf-8"),
                            capture_output=True, timeout=DELAI + 5)
        except TimeoutExpired as exc:
            raise ErreurAPI("timeout", "Le client HTTP a dépassé le délai maximal.", perf_counter() - debut) from exc
        except OSError as exc:
            raise ErreurAPI("client_http", "Impossible de lancer le client curl.", perf_counter() - debut) from exc
        corps, _, statistiques = processus.stdout.rpartition(b"\n")
        try:
            statut, duree = statistiques.split()
            statut, duree = int(statut), float(duree)
        except ValueError:
            statut, duree = None, perf_counter() - debut
        if processus.returncode:
            code = "timeout" if processus.returncode == 28 else "reseau"
            raise ErreurAPI(code, f"Échec du transport HTTP (curl {processus.returncode}).", duree)
        if statut is None:
            raise ErreurAPI("api_illisible", "Le client HTTP n’a pas renvoyé de statut lisible.", duree)
        if not 200 <= statut < 300:
            raise ErreurAPI(f"http_{statut}", f"LM Studio a renvoyé un statut HTTP {statut}.", duree)
        try:
            reponse = json.loads(corps)
        except (UnicodeError, ValueError) as exc:
            raise ErreurAPI("api_illisible", "La réponse HTTP ne contient pas de JSON lisible.", duree) from exc
        if not isinstance(reponse, dict):
            raise ErreurAPI("api_illisible", "Objet JSON attendu dans la réponse HTTP.", duree)
        return reponse, duree

    def choisir_modele(self, identifiant):
        reponse, _ = self.requete("models")
        modeles = [modele for modele in reponse["models"] if modele["type"] == "llm"
                   and "gemma4e2b" in "".join(c for c in modele["key"].lower() if c.isalnum())
                   and (identifiant is None or modele["key"] == identifiant)]
        if len(modeles) != 1:
            raise ValueError("Un seul Gemma 4 E2B doit être identifié. Préciser --model-id si nécessaire.")
        modele = modeles[0]
        modes = modele.get("capabilities", {}).get("reasoning", {}).get("allowed_options")
        if modes is not None and PARAMETRES["reasoning"] not in modes:
            raise ValueError("Le modèle chargé ne permet pas le réglage reasoning=off approuvé.")
        instances = modele["loaded_instances"]
        if not instances:
            self.requete("models/load", {"model": modele["key"], "context_length": PARAMETRES["context_length"]})
            reponse, _ = self.requete("models")
            instances = next(item["loaded_instances"] for item in reponse["models"] if item["key"] == modele["key"])
        instances = [instance for instance in instances
                     if instance["config"]["context_length"] == PARAMETRES["context_length"]]
        if len(instances) != 1:
            raise ValueError("Une seule instance Gemma 4 E2B doit être chargée avec un contexte de 4 096 tokens.")
        informations = {cle: modele.get(cle) for cle in ("key", "publisher", "architecture", "quantization",
                                                         "selected_variant", "size_bytes", "format")}
        return informations, instances[0]

    def generer(self, instance_id, prompt):
        reponse, duree = self.requete("chat", {"model": instance_id, "input": prompt, **PARAMETRES})
        try:
            if reponse["model_instance_id"] != instance_id:
                raise ErreurAPI("instance_modele", "LM Studio a utilisé une autre instance de modèle.", duree)
            sortie = reponse["output"]
            if not isinstance(sortie, list):
                raise TypeError("output doit être une liste.")
            texte = "\n".join(item["content"] for item in sortie if item["type"] == "message")
        except (KeyError, TypeError) as exc:
            raise ErreurAPI("api_illisible", "Le schéma de sortie LM Studio est inattendu.", duree) from exc
        return texte, duree


def initialiser_journal(db, configuration):
    db.execute("CREATE TABLE IF NOT EXISTS experience (configuration VARCHAR PRIMARY KEY)")
    configurations = db.execute("SELECT configuration FROM experience").fetchall()
    if configurations and configurations != [(configuration,)]:
        raise ValueError("Les empreintes, la version des prompts ou la configuration diffèrent du journal.")
    if not configurations:
        db.execute("INSERT INTO experience VALUES (?)", [configuration])
    db.execute("""
        CREATE TABLE IF NOT EXISTS tentatives (
            inference_id UUID PRIMARY KEY, question_id VARCHAR NOT NULL, pilot_order INTEGER NOT NULL,
            model_id VARCHAR NOT NULL, prompt_id VARCHAR NOT NULL, segment_id UUID NOT NULL,
            raw_response VARCHAR, response_time DOUBLE,
            status VARCHAR NOT NULL, error_type VARCHAR, error_message VARCHAR,
            configuration VARCHAR NOT NULL, UNIQUE (prompt_id, question_id)
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS segments (
            segment_id UUID PRIMARY KEY, prompt_id VARCHAR NOT NULL, started_at TIMESTAMPTZ NOT NULL,
            ended_at TIMESTAMPTZ, active_seconds DOUBLE NOT NULL
        )
    """)
    db.execute("""
        UPDATE tentatives SET status = 'interrupted', error_type = 'interruption',
            error_message = 'La tentative a été réservée mais sa réception est indéterminée.'
        WHERE status = 'in_progress'
    """)


def chemin_bronze(prompt_id, stockage=STOCKAGE_PILOTE):
    return stockage.bronze / FICHIERS_RESULTATS[prompt_id].name


def exporter_bronze(db, prompt_id, modele, stockage=STOCKAGE_PILOTE):
    destination = chemin_bronze(prompt_id, stockage)
    colonnes = ", ".join(nom for nom, _ in SCHEMA_BRONZE)
    with TemporaryDirectory(dir=destination.parent) as temporaire:
        parquet = Path(temporaire) / destination.name
        db.sql(f"""
            SELECT {colonnes} FROM tentatives
            WHERE model_id = ? AND prompt_id = ? AND status <> 'in_progress' ORDER BY pilot_order
        """, params=[modele, prompt_id]).write_parquet(str(parquet))
        if destination.exists() and empreinte_fichier(destination) == empreinte_fichier(parquet):
            return
        parquet.replace(destination)


def structurer_silver(questions, prompt_id, stockage=STOCKAGE_PILOTE):
    bronze = chemin_bronze(prompt_id, stockage)
    destination = stockage.silver / FICHIERS_RESULTATS[prompt_id].name
    with duckdb.connect(":memory:") as db, TemporaryDirectory(dir=destination.parent) as temporaire:
        empreinte_bronze = empreinte_fichier(bronze)
        db.execute("CREATE TEMP TABLE tentatives_brutes AS SELECT * FROM read_parquet(?)", [str(bronze)])
        brutes = db.table("tentatives_brutes")
        if tuple(zip(brutes.columns, map(str, brutes.types), strict=True)) != SCHEMA_BRONZE:
            raise ValueError(f"Schéma Bronze inattendu : {bronze.name}.")
        donnees = brutes.project("inference_id, pilot_order, question_id, model_id, prompt_id, raw_response, status")
        notes = []
        rangs, identifiants, modeles = set(), set(), set()
        for inference_id, rang, question_id, modele, prompt, brute, statut in donnees.fetchall():
            if (prompt != prompt_id or rang in rangs or inference_id in identifiants
                    or not 1 <= rang <= len(questions) or questions[rang - 1]["question_id"] != question_id):
                raise ValueError(f"Tentative Bronze incohérente avec le manifeste : {inference_id}.")
            rangs.add(rang)
            identifiants.add(inference_id)
            modeles.add(modele)
            if (statut == "received" and brute is None) or statut not in {"received", "technical_error", "interrupted"}:
                raise ValueError(f"Réponse Bronze incohérente : {inference_id}.")
            evaluation = score(brute, questions[rang - 1]) if statut == "received" else (None, None, None)
            notes.append((str(inference_id), *evaluation))
        if len(modeles) > 1:
            raise ValueError(f"Plusieurs modèles dans la table Bronze {bronze.name}.")
        evaluations = pd.DataFrame.from_records(
            notes, columns=["inference_id", "ai_answer", "ai_correct", "format_valid"],
        ).astype({"inference_id": "string", "ai_answer": "string", "ai_correct": "boolean", "format_valid": "boolean"})
        db.register("evaluations", evaluations)
        parquet = Path(temporaire) / destination.name
        db.sql("""
            SELECT b.question_id, b.model_id, b.prompt_id, b.inference_id, b.raw_response,
                   e.ai_answer, e.ai_correct, b.response_time, e.format_valid, b.status,
                   b.configuration, b.error_type, b.error_message
            FROM tentatives_brutes b JOIN evaluations e ON b.inference_id = CAST(e.inference_id AS UUID)
            ORDER BY b.pilot_order
        """).write_parquet(str(parquet))
        if empreinte_fichier(bronze) != empreinte_bronze:
            raise ValueError(f"La table Bronze {bronze.name} a changé pendant la structuration.")
        if destination.exists() and empreinte_fichier(destination) == empreinte_fichier(parquet):
            return
        parquet.replace(destination)


def exporter(db, questions, prompt_id, modele, stockage=STOCKAGE_PILOTE):
    exporter_bronze(db, prompt_id, modele, stockage)
    structurer_silver(questions, prompt_id, stockage)


def executer_bloc(db, client, questions, prompt_id, modele, instance_id, configuration, stockage=STOCKAGE_PILOTE):
    terminees = {ligne[0] for ligne in db.execute(
        "SELECT question_id FROM tentatives WHERE prompt_id = ?", [prompt_id]
    ).fetchall()}
    restantes = [(rang, question) for rang, question in enumerate(questions, 1)
                 if question["question_id"] not in terminees]
    if not restantes:
        exporter(db, questions, prompt_id, modele, stockage)
        return

    client.generer(instance_id, construire_prompt(QUESTION_ECHAUFFEMENT, "P1_choices"))
    segment = str(uuid4())
    db.execute("INSERT INTO segments VALUES (?, ?, ?, NULL, 0)", [segment, prompt_id, datetime.now(timezone.utc)])
    debut = perf_counter()
    print(f"{prompt_id} · {len(terminees)}/{len(questions)} positions déjà journalisées.", flush=True)
    try:
        for index, (rang, question) in enumerate(restantes, 1):
            inference_id = str(uuid4())
            db.execute("""
                INSERT INTO tentatives (inference_id, question_id, pilot_order, model_id, prompt_id,
                    segment_id, status, configuration) VALUES (?, ?, ?, ?, ?, ?, 'in_progress', ?)
            """, [inference_id, question["question_id"], rang, modele, prompt_id, segment, configuration])
            try:
                brute, duree = client.generer(instance_id, construire_prompt(question, prompt_id))
                resultat = (brute, duree, "received", None, None)
            except ErreurAPI as exc:
                resultat = (None, exc.duree, "technical_error", exc.code, str(exc))
            db.execute("""
                UPDATE tentatives SET raw_response = ?, response_time = ?, status = ?,
                    error_type = ?, error_message = ? WHERE inference_id = ?
            """, [*resultat, inference_id])
            if index % INTERVALLE_EXPORT == 0:
                exporter(db, questions, prompt_id, modele, stockage)
                print(f"{prompt_id} · {len(terminees) + index}/{len(questions)} positions journalisées.", flush=True)
            db.execute("UPDATE segments SET active_seconds = ? WHERE segment_id = ?", [perf_counter() - debut, segment])
            if resultat[-2] in {"client_http", "instance_modele", "http_401", "http_403", "http_404"}:
                raise RuntimeError(f"Bloc suspendu après l’erreur {resultat[-2]}.")
    finally:
        exporter(db, questions, prompt_id, modele, stockage)
        db.execute("UPDATE segments SET active_seconds = ?, ended_at = ? WHERE segment_id = ?",
                   [perf_counter() - debut, datetime.now(timezone.utc), segment])
    print(f"{prompt_id} · bloc terminé en {perf_counter() - debut:.2f} s.", flush=True)


def configuration_execution(args, meta, prompts=PROMPTS_HISTORIQUES):
    client = LMStudio(args.url, args.curl)
    modele, instance = client.choisir_modele(args.model_id)
    configurations_prompts = {
        prompt: empreinte(*(construire_prompt({"type": type_question, "question": "{question}",
                                               "answer_choices": [f"{{choix_{i}}}" for i in range(len(reponses))]},
                                              prompt)
                             for type_question, reponses in REPONSES_ADMISES.items()))
        for prompt in prompts
    }
    configuration = json_compact({
        "dataset_sha256": meta["dataset_sha256"], "manifest_sha256": meta["manifest_sha256"],
        "prompt_sha256": configurations_prompts, "model": modele, "instance": instance,
        "generation": PARAMETRES, "timeout_seconds": DELAI, "api": f"{client.adresse}/api/v1/chat",
        "lm_studio_version": args.lm_studio_version, "runtime": args.runtime,
        "transport": Path(args.curl).name, "export_every": INTERVALLE_EXPORT,
    })
    return client, modele, instance, configuration


def executer(args, questions, meta, stockage=STOCKAGE_PILOTE, prompts=PROMPTS_HISTORIQUES, reference=None):
    if not stockage.journal.exists() and any(chemin_bronze(prompt, stockage).exists()
            or (stockage.silver / FICHIERS_RESULTATS[prompt].name).exists() for prompt in prompts):
        raise ValueError("Récupérer le journal de reprise d’origine avant de reprendre des résultats existants.")
    client, modele, instance, configuration = configuration_execution(args, meta, prompts)
    if reference is not None:
        actuelle = json.loads(configuration)
        differences = sorted(cle for cle in reference.keys() | actuelle.keys()
                             if cle != "prompt_sha256" and reference.get(cle) != actuelle.get(cle))
        if differences:
            raise ValueError(f"La configuration diffère du pilote pour {', '.join(differences)}.")
    with duckdb.connect(str(stockage.journal)) as db:
        initialiser_journal(db, configuration)
        for prompt in prompts:
            executer_bloc(db, client, questions, prompt, modele["key"], instance["id"], configuration, stockage)


def configuration_journal(db, meta):
    [(configuration,)] = db.execute("SELECT configuration FROM experience").fetchall()
    config = json.loads(configuration)
    if any(config[cle] != meta[cle] for cle in ("dataset_sha256", "manifest_sha256")):
        raise ValueError("Le journal de reprise ne correspond pas au Silver et au manifeste actifs.")
    return config


def executer_p3(args, questions, meta):
    with duckdb.connect(str(JOURNAL), read_only=True) as db:
        reference = configuration_journal(db, meta)
    runtimes = check_output([args.lms, "runtime", "ls"], encoding="utf-8", timeout=15)
    selectionnes = {ligne.split()[0] for ligne in runtimes.splitlines() if "✓" in ligne}
    if args.runtime != reference["runtime"] or args.runtime not in selectionnes:
        raise ValueError(f"Le moteur {reference['runtime']} doit être sélectionné dans LM Studio.")
    executer(args, questions, meta, STOCKAGE_P3, (PROMPT_P3,), reference)


def reconstruire_bronze(meta):
    with duckdb.connect(str(JOURNAL), read_only=True) as db:
        modele = configuration_journal(db, meta)["model"]["key"]
        for prompt in PROMPTS_HISTORIQUES:
            exporter_bronze(db, prompt, modele)


def mesures_bilan(questions, meta, stockage, prompts):
    par_id = {question["question_id"]: question for question in questions}
    statistiques_prompts, recus = {}, {}
    with duckdb.connect(str(stockage.journal), read_only=True) as db:
        configuration_journal(db, meta)
        for prompt in prompts:
            lignes = db.execute("""
                SELECT question_id, raw_response, response_time, status, error_type
                FROM tentatives WHERE prompt_id = ? ORDER BY pilot_order
            """, [prompt]).fetchall()
            recus[prompt] = {qid: (*score(brute, par_id[qid])[1:], temps) for qid, brute, temps, statut, _ in lignes
                            if statut == "received"}
            mesures = recus[prompt].values()
            latences = [temps for _, _, temps in mesures]
            correctes = sum(correct for correct, _, _ in mesures)
            conformes = sum(conforme for _, conforme, _ in mesures)
            erreurs = Counter(erreur for *_, statut, erreur in lignes if statut == "technical_error")
            interrompues = sum(statut in {"in_progress", "interrupted"} for *_, statut, _ in lignes)
            tentatives = len(mesures) + erreurs.total()
            duree, = db.execute("SELECT COALESCE(SUM(active_seconds), 0) FROM segments WHERE prompt_id = ?",
                                [prompt]).fetchone()
            complet = tentatives == len(questions)
            restantes = meta["population"] - (tentatives if prompt == PROMPT_P3 else len(mesures))
            statistiques = {
                "tentatives_mesurees": tentatives, "recues": len(mesures), "correctes": correctes,
                "conformes": conformes, "exactitude": correctes / len(mesures) if mesures else None,
                "conformite": conformes / len(mesures) if mesures else None,
                "erreurs_techniques": dict(erreurs), "interrompues": interrompues,
                "taux_erreur_technique": erreurs.total() / tentatives if tentatives else None,
                "latence_moyenne_s": mean(latences) if latences else None,
                "latence_mediane_s": median(latences) if latences else None, "duree_active_s": duree,
                "projection_complete_s": duree * meta["population"] / len(questions) if complet else None,
                "projection_restante_s": duree * restantes / len(questions) if complet else None,
            }
            groupes = {}
            for dimension in COLONNES_STRATES:
                groupes[dimension] = {}
                for qid, (correct, conforme, _) in recus[prompt].items():
                    groupe = groupes[dimension].setdefault(par_id[qid][dimension], Counter())
                    groupe.update(recues=1, correctes=int(correct), conformes=int(conforme))
            statistiques["groupes"] = groupes
            statistiques_prompts[prompt] = statistiques
    return statistiques_prompts, recus


def comparer_reponses(p1, p2):
    partagees = p1.keys() & p2.keys()
    return {
        "questions_communes": len(partagees),
        "p1_correctes": sum(p1[qid][0] for qid in partagees),
        "p2_correctes": sum(p2[qid][0] for qid in partagees),
        "p1_seul_correct": sum(p1[qid][0] and not p2[qid][0] for qid in partagees),
        "p2_seul_correct": sum(p2[qid][0] and not p1[qid][0] for qid in partagees),
    }


def bilan(questions, meta, stockage=STOCKAGE_PILOTE, *, inclure_p3=False):
    statistiques, recus = mesures_bilan(questions, meta, stockage, PROMPTS_HISTORIQUES)
    rapport = {"population": meta["population"], "sample_size": len(questions), "prompts": statistiques}
    rapport["apparie"] = comparer_reponses(*recus.values())
    if inclure_p3:
        statistiques_p3, recus_p3 = mesures_bilan(questions, meta, STOCKAGE_P3, (PROMPT_P3,))
        statistiques.update(statistiques_p3)
        recus.update(recus_p3)
        rapport["paires"] = [
            {"prompts": [premier, second], **comparer_reponses(recus[premier], recus[second])}
            for premier, second in combinations(recus, 2)
        ]
    return rapport


def main():
    parser = ArgumentParser(description="Pilote Gemma 4 E2B sur le Silver OpenTDB définitif.")
    sous_commandes = parser.add_subparsers(dest="action", required=True)
    sous_commandes.add_parser("manifeste", help="Créer ou contrôler le manifeste du Silver définitif")
    lancement = sous_commandes.add_parser("executer", help="Exécuter ou reprendre les deux blocs")
    ajouter_options_lm_studio(lancement)
    lancement_p3 = sous_commandes.add_parser("executer-p3", help="Exécuter ou reprendre uniquement P3 sur le pilote")
    ajouter_options_lm_studio(lancement_p3)
    lancement_p3.add_argument("--lms", default="lms")
    sous_commandes.add_parser("bilan", help="Afficher les métriques et les projections du journal")
    sous_commandes.add_parser("bilan-p3", help="Comparer les trois prompts à partir des journaux du pilote")
    sous_commandes.add_parser("reconstruire-bronze", help="Exporter les mesures brutes du journal hors ligne")
    sous_commandes.add_parser("structurer", help="Reproduire les Parquet Silver à partir du Bronze hors ligne")
    args = parser.parse_args()
    try:
        if args.action == "manifeste":
            questions, meta = preparer_manifeste()
            print(f"{len(questions)} identifiants · {MANIFESTE.relative_to(RACINE)}")
            print(f"SHA-256 manifeste · {meta['manifest_sha256']}")
            return
        questions, meta = charger_manifeste(charger_silver())
        if args.action == "reconstruire-bronze":
            reconstruire_bronze(meta)
            return
        if args.action == "structurer":
            for prompt in PROMPTS_HISTORIQUES:
                structurer_silver(questions, prompt)
            return
        if args.action == "executer":
            executer(args, questions, meta)
        if args.action == "executer-p3":
            executer_p3(args, questions, meta)
        rapport = bilan(questions, meta, inclure_p3=args.action in {"executer-p3", "bilan-p3"})
        print(json.dumps(rapport, indent=2, ensure_ascii=False))
    except (ErreurAPI, OSError, RuntimeError, SubprocessError, ValueError) as exc:
        parser.exit(1, f"Erreur : {exc}\n")


def ajouter_options_lm_studio(parser):
    parser.add_argument("--url", default="http://127.0.0.1:1234")
    parser.add_argument("--curl", default="curl")
    parser.add_argument("--model-id")
    parser.add_argument("--lm-studio-version", required=True)
    parser.add_argument("--runtime", required=True)


if __name__ == "__main__":
    main()
