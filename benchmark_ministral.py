from argparse import ArgumentParser
import json
from pathlib import Path
from shutil import copy2
from subprocess import SubprocessError, check_output
from tempfile import TemporaryDirectory

import duckdb

import benchmark_gemma as gemma
import pilote_gemma as pipeline
import pilote_ministral as pilote


DOSSIER = pipeline.SILVER.parent / "benchmark_ministral_lot4"
STOCKAGE = pipeline.StockageInference(
    DOSSIER / "benchmark.duckdb", pipeline.BRONZE.parent / DOSSIER.name, DOSSIER, "ministral"
)


def charger_plan():
    questions, manifeste_gemma, _ = gemma.charger_plan()
    echantillon, meta_pilote = pilote.charger_manifeste()
    if questions[:len(echantillon)] != echantillon or manifeste_gemma["dataset_sha256"] != meta_pilote["dataset_sha256"]:
        raise ValueError("Les 30 questions du pilote Ministral doivent ouvrir le manifeste complet Gemma.")
    meta = {**manifeste_gemma, "pilot_size": len(echantillon), "pilot_manifest_sha256": meta_pilote["manifest_sha256"]}
    return questions, meta, manifeste_gemma, meta_pilote


def preparer(questions, meta, meta_pilote):
    source = pilote.STOCKAGE.journal
    if source.with_suffix(".duckdb.wal").exists():
        raise ValueError("Fermer le journal du pilote avant de reprendre ses mesures.")
    attendues = sorted((prompt, rang, question["question_id"], "received")
                      for prompt in pilote.PROMPTS for rang, question in enumerate(questions[:meta["pilot_size"]], 1))
    with duckdb.connect(str(source), read_only=True) as db:
        configuration = pipeline.configuration_journal(db, meta_pilote)
        lignes = db.execute("""
            SELECT prompt_id, pilot_order, question_id, status FROM tentatives ORDER BY prompt_id, pilot_order
        """).fetchall()
        if lignes != attendues:
            raise ValueError("Les 90 mesures attendues du pilote Ministral sont requises pour lancer le benchmark.")
        if not STOCKAGE.journal.is_file():
            if any(pipeline.chemin_bronze(prompt, STOCKAGE).exists()
                   or (DOSSIER / STOCKAGE.nom_fichier(prompt)).exists() for prompt in pilote.PROMPTS):
                raise ValueError("Récupérer le journal de reprise avant de continuer le benchmark Ministral.")
            DOSSIER.mkdir(parents=True, exist_ok=True)
            with TemporaryDirectory(dir=DOSSIER) as temporaire:
                journal = Path(temporaire) / STOCKAGE.journal.name
                copy2(source, journal)
                config = {**configuration, "manifest_sha256": meta["manifest_sha256"]}
                with duckdb.connect(str(journal)) as copie:
                    copie.execute("UPDATE experience SET configuration = ?", [pipeline.json_compact(config)])
                STOCKAGE.journal.hardlink_to(journal)
    return {**configuration, "manifest_sha256": meta["manifest_sha256"]}


def executer(args, questions, meta, meta_pilote):
    reference = preparer(questions, meta, meta_pilote)
    runtimes = check_output([args.lms, "runtime", "ls"], encoding="utf-8", timeout=15)
    selectionnes = {ligne.split()[0] for ligne in runtimes.splitlines() if "✓" in ligne}
    if reference["runtime"] != args.runtime or args.runtime not in selectionnes:
        raise ValueError(f"Sélectionner le moteur du pilote ({reference['runtime']}).")
    client = pilote.LMMinistral(args.url, args.curl)
    _, _, _, configuration = pipeline.configuration_execution(args, meta, pilote.PROMPTS, client=client)
    actuelle = json.loads(configuration)
    differences = sorted(cle for cle in reference.keys() | actuelle.keys() if reference.get(cle) != actuelle.get(cle))
    if differences:
        raise ValueError(f"La configuration diffère du pilote pour {', '.join(differences)}.")
    with duckdb.connect(str(STOCKAGE.journal), read_only=True) as db:
        if pipeline.configuration_journal(db, meta) != reference:
            raise ValueError("La configuration du journal complet diffère du pilote.")
    STOCKAGE.bronze.mkdir(parents=True, exist_ok=True)
    print(f"Configuration du pilote confirmée · {pilote.INSTANCE} · {args.runtime}", flush=True)
    pipeline.executer(args, questions, meta, STOCKAGE, pilote.PROMPTS, reference, client=client)


def bilan(questions, meta, meta_gemma, meta_pilote):
    ministral, recus_ministral = pipeline.mesures_bilan(questions, meta, STOCKAGE, pilote.PROMPTS)
    pilote_ministral, _ = pipeline.mesures_bilan(questions, meta_pilote, pilote.STOCKAGE, pilote.PROMPTS)
    mesures_gemma, recus_gemma = pipeline.mesures_bilan(questions, meta_gemma, gemma.STOCKAGE, pipeline.PROMPTS_HISTORIQUES)
    mesures_p3, recus_p3 = pipeline.mesures_bilan(questions, meta_gemma, gemma.STOCKAGE_P3, gemma.PROMPTS_P3)
    mesures_gemma.update(mesures_p3)
    recus_gemma.update(recus_p3)

    for prompt, mesures in ministral.items():
        mesures["duree_active_complement_s"] = mesures["duree_active_s"] - pilote_ministral[prompt]["duree_active_s"]
    comparaison = {}
    for prompt in pilote.PROMPTS:
        appariement = pipeline.comparer_reponses(recus_gemma[prompt], recus_ministral[prompt])
        comparaison[prompt] = {
            "questions_communes": appariement["questions_communes"],
            "gemma_correctes": appariement["p1_correctes"],
            "ministral_correctes": appariement["p2_correctes"],
            "gemma_seul_correct": appariement["p1_seul_correct"],
            "ministral_seul_correct": appariement["p2_seul_correct"],
        }
    return {"population": len(questions), "ministral": ministral, "gemma": mesures_gemma, "comparaison": comparaison}


def main():
    parser = ArgumentParser(description="Benchmark Ministral Instruct sur les 5 290 questions du lot 4.")
    actions = parser.add_subparsers(dest="action", required=True)
    actions.add_parser("preparer", help="Reprendre les 90 mesures du pilote hors réseau")
    actions.add_parser("bilan", help="Lire le journal et comparer les benchmarks")
    execution = actions.add_parser("executer", help="Démarrer ou reprendre les inférences restantes")
    pipeline.ajouter_options_lm_studio(execution)
    execution.add_argument("--lms", default="lms")
    execution.set_defaults(model_id=pilote.MODELE, runtime=pilote.MOTEUR)
    args = parser.parse_args()
    try:
        questions, meta, meta_gemma, meta_pilote = charger_plan()
        if args.action == "preparer":
            preparer(questions, meta, meta_pilote)
            print(f"{len(questions)} questions dans l’ordre Gemma · {meta['pilot_size']} mesures reprises par prompt.")
        elif args.action == "executer":
            executer(args, questions, meta, meta_pilote)
        else:
            print(json.dumps(bilan(questions, meta, meta_gemma, meta_pilote), ensure_ascii=False, indent=2))
    except (OSError, pipeline.ErreurAPI, RuntimeError, SubprocessError, ValueError) as exc:
        parser.exit(1, f"Erreur du benchmark Ministral ({exc})\n")


if __name__ == "__main__":
    main()
