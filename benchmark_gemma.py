from argparse import ArgumentParser
import json
from pathlib import Path
from shutil import copy2
from subprocess import SubprocessError, check_output
from tempfile import TemporaryDirectory

import duckdb
import pandas as pd

import pilote_gemma as pilote
from preparer_silver import BRONZE, SILVER, empreinte_fichier, ecrire_parquet, lire_parquet


DOSSIER = SILVER.parent / "benchmark_lot4"
STOCKAGE = pilote.StockageInference(DOSSIER / "benchmark.duckdb", BRONZE.parent / DOSSIER.name, DOSSIER)
STOCKAGE_P3 = pilote.StockageInference(DOSSIER / "benchmark_p3.duckdb", STOCKAGE.bronze, STOCKAGE.silver)
PROMPTS_P3 = (pilote.PROMPT_P3,)
MANIFESTE = DOSSIER / "question_ids.parquet"
METADONNEES = DOSSIER / "manifest_metadata.json"
SCHEMA = (("pilot_order", "BIGINT"), ("question_id", "VARCHAR"))


def plan():
    questions = pilote.charger_silver()
    echantillon, meta_pilote = pilote.charger_manifeste(questions)
    ids_pilote = {question["question_id"] for question in echantillon}
    ordre = echantillon + [question for question in questions if question["question_id"] not in ids_pilote]
    manifeste = pd.DataFrame({"pilot_order": range(1, len(ordre) + 1),
                              "question_id": [question["question_id"] for question in ordre]})
    return ordre, manifeste, meta_pilote


def charger_plan():
    questions, attendu, meta_pilote = plan()
    meta = json.loads(METADONNEES.read_text(encoding="utf-8"))
    if (meta["dataset_sha256"] != meta_pilote["dataset_sha256"]
            or meta["pilot_manifest_sha256"] != meta_pilote["manifest_sha256"]
            or meta["manifest_sha256"] != empreinte_fichier(MANIFESTE)
            or meta["population"] != len(questions)
            or lire_parquet(MANIFESTE, SCHEMA) != attendu.to_dict("records")):
        raise ValueError("Le manifeste du lot 4 ne correspond pas au Silver et au pilote conservé.")
    if not STOCKAGE.journal.is_file():
        raise FileNotFoundError("Journal de reprise du lot 4 manquant.")
    return questions, meta, meta_pilote


def preparer():
    if DOSSIER.exists():
        return charger_plan()
    questions, manifeste, meta_pilote = plan()
    if pilote.JOURNAL.with_suffix(".duckdb.wal").exists():
        raise ValueError("Le journal du pilote doit être fermé avant sa reprise dans le lot 4.")
    total_pilote = meta_pilote["sample_size"]
    reference = [(rang, question["question_id"], "received")
                 for rang, question in enumerate(questions[:total_pilote], 1)]
    with TemporaryDirectory(dir=DOSSIER.parent) as temporaire:
        dossier = Path(temporaire) / DOSSIER.name
        dossier.mkdir()
        parquet = dossier / MANIFESTE.name
        ecrire_parquet(manifeste, parquet)
        meta = {
            "dataset_sha256": meta_pilote["dataset_sha256"],
            "manifest_sha256": empreinte_fichier(parquet),
            "pilot_manifest_sha256": meta_pilote["manifest_sha256"],
            "population": len(questions), "pilot_size": total_pilote,
            "order": "Ordre du pilote puis ordre du Silver révisé",
        }
        (dossier / METADONNEES.name).write_text(pilote.json_compact(meta) + "\n", encoding="utf-8")
        journal = dossier / STOCKAGE.journal.name
        with duckdb.connect(str(pilote.JOURNAL), read_only=True) as db:
            config = pilote.configuration_journal(db, meta_pilote)
            for prompt in pilote.PROMPTS_HISTORIQUES:
                lignes = db.execute("""
                    SELECT pilot_order, question_id, status FROM tentatives WHERE prompt_id = ? ORDER BY pilot_order
                """, [prompt]).fetchall()
                if lignes != reference:
                    raise ValueError(f"Le journal du pilote ne contient pas les réponses attendues pour {prompt}.")
            copy2(pilote.JOURNAL, journal)
        config["manifest_sha256"] = meta["manifest_sha256"]
        with duckdb.connect(str(journal)) as db:
            db.execute("UPDATE experience SET configuration = ?", [pilote.json_compact(config)])
        dossier.rename(DOSSIER)
    return charger_plan()


def preparer_p3(questions, meta, meta_pilote):
    if STOCKAGE_P3.journal.is_file():
        with duckdb.connect(str(STOCKAGE_P3.journal), read_only=True) as db:
            pilote.configuration_journal(db, meta)
        return
    fichier = pilote.FICHIERS_RESULTATS[pilote.PROMPT_P3].name
    if any((dossier / fichier).exists() for dossier in (STOCKAGE_P3.bronze, STOCKAGE_P3.silver)):
        raise ValueError("Récupérer le journal de reprise P3 avant de reprendre des résultats existants.")
    source = pilote.STOCKAGE_P3.journal
    if source.with_suffix(".duckdb.wal").exists():
        raise ValueError("Le journal du pilote P3 doit être fermé avant sa reprise dans le lot 4.")
    attendues = [(rang, question["question_id"], pilote.PROMPT_P3, "received")
                 for rang, question in enumerate(questions[:meta_pilote["sample_size"]], 1)]
    with TemporaryDirectory(dir=DOSSIER) as temporaire:
        journal = Path(temporaire) / STOCKAGE_P3.journal.name
        with duckdb.connect(str(source), read_only=True) as db:
            configuration = pilote.configuration_journal(db, meta_pilote)
            lignes = db.execute("""
                SELECT pilot_order, question_id, prompt_id, status FROM tentatives ORDER BY pilot_order
            """).fetchall()
            if lignes != attendues:
                raise ValueError("Le journal du pilote P3 ne contient pas les 530 réponses attendues.")
            copy2(source, journal)
        configuration["manifest_sha256"] = meta["manifest_sha256"]
        with duckdb.connect(str(journal)) as db:
            db.execute("UPDATE experience SET configuration = ?", [pilote.json_compact(configuration)])
        STOCKAGE_P3.journal.hardlink_to(journal)


def verifier(args, meta, meta_pilote, stockage=STOCKAGE, source=pilote.JOURNAL,
             prompts=pilote.PROMPTS_HISTORIQUES):
    with duckdb.connect(str(source), read_only=True) as db:
        attendue = pilote.configuration_journal(db, meta_pilote)
    runtimes = check_output([args.lms, "runtime", "ls"], encoding="utf-8", timeout=15)
    selectionnes = {ligne.split()[0] for ligne in runtimes.splitlines() if "✓" in ligne}
    if args.runtime != attendue["runtime"] or args.runtime not in selectionnes:
        raise ValueError(f"Le moteur {attendue['runtime']} doit être sélectionné dans LM Studio.")
    _, _, _, configuration = pilote.configuration_execution(args, meta, prompts)
    attendue["manifest_sha256"] = meta["manifest_sha256"]
    actuelle = json.loads(configuration)
    differences = sorted(cle for cle in attendue.keys() | actuelle.keys() if attendue.get(cle) != actuelle.get(cle))
    if differences:
        raise ValueError(f"La configuration diffère du pilote pour {', '.join(differences)}.")
    with duckdb.connect(str(stockage.journal), read_only=True) as db:
        if pilote.configuration_journal(db, meta) != attendue:
            raise ValueError("La configuration du journal du lot 4 diffère de celle du pilote.")
    print(f"Configuration compatible avec le pilote · {actuelle['instance']['id']} · {args.runtime}", flush=True)


def main():
    parser = ArgumentParser(description="Benchmark Gemma 4 E2B sur les 5 290 questions Silver.")
    commandes = parser.add_subparsers(dest="action", required=True)
    preparation = commandes.add_parser("preparer", help="Construire le manifeste et reprendre les mesures du pilote hors réseau")
    preparation.add_argument("--p3", action="store_true", help="Reprendre les mesures du pilote P3")
    bilan = commandes.add_parser("bilan", help="Calculer les métriques à partir des journaux du lot 4")
    bilan.add_argument("--p3", action="store_true", help="Inclure P3 dans le bilan")
    for action in ("verifier", "executer"):
        commande = commandes.add_parser(action)
        pilote.ajouter_options_lm_studio(commande)
        commande.add_argument("--lms", default="lms")
        commande.add_argument("--p3", action="store_true", help="Utiliser uniquement le journal et le prompt P3")
    args = parser.parse_args()
    try:
        if args.action == "preparer" and not args.p3:
            questions, meta, _ = preparer()
            print(f"{len(questions)} questions · {meta['pilot_size']} déjà mesurées par prompt.")
            return
        questions, meta, meta_pilote = charger_plan()
        stockage, source, prompts = STOCKAGE, pilote.JOURNAL, pilote.PROMPTS_HISTORIQUES
        if args.p3:
            stockage, source, prompts = STOCKAGE_P3, pilote.STOCKAGE_P3.journal, PROMPTS_P3
            if args.action in {"preparer", "executer"}:
                preparer_p3(questions, meta, meta_pilote)
        if args.action == "preparer":
            print(f"{len(questions)} questions · {meta['pilot_size']} mesures P3 reprises.")
            return
        if args.action in {"verifier", "executer"}:
            verifier(args, meta, meta_pilote, stockage, source, prompts)
        if args.action == "executer":
            stockage.bronze.mkdir(parents=True, exist_ok=True)
            pilote.executer(args, questions, meta, stockage, prompts)
        if args.action in {"bilan", "executer"}:
            rapport = pilote.bilan(questions, meta, STOCKAGE, inclure_p3=args.p3, stockage_p3=STOCKAGE_P3)
            print(json.dumps(rapport, ensure_ascii=False, indent=2))
    except (OSError, pilote.ErreurAPI, RuntimeError, SubprocessError, ValueError) as exc:
        parser.exit(1, f"Erreur : {exc}\n")


if __name__ == "__main__":
    main()
