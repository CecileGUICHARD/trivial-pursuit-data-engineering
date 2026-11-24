from argparse import ArgumentParser
import json
from statistics import mean
from subprocess import SubprocessError, check_output

import pandas as pd

import pilote_gemma as pipeline


MODELE = "prism-ml/bonsai-27b"
VARIANTE = f"{MODELE}@q1_0"
INSTANCE = "bonsai-pilote"
TAILLE = 30
PROMPTS = (*pipeline.PROMPTS_HISTORIQUES, pipeline.PROMPT_P3)
DOSSIER = pipeline.SILVER.parent / "pilote_bonsai"
STOCKAGE = pipeline.StockageInference(
    DOSSIER / "pilot.duckdb", pipeline.BRONZE.parent / DOSSIER.name, DOSSIER, "bonsai"
)
MANIFESTE = DOSSIER / "pilot_question_ids.parquet"


class LMBonsai(pipeline.LMStudio):
    def choisir_modele(self, identifiant):
        reponse, _ = self.requete("models")
        modeles = [modele for modele in reponse["models"] if modele["key"] == identifiant]
        if len(modeles) != 1 or modeles[0].get("selected_variant") != VARIANTE:
            raise ValueError(f"La variante {VARIANTE} doit être sélectionnée dans LM Studio.")
        modele = modeles[0]
        modes = modele.get("capabilities", {}).get("reasoning", {}).get("allowed_options", [])
        if pipeline.PARAMETRES["reasoning"] not in modes:
            raise ValueError("Bonsai doit accepter le réglage reasoning=off.")
        instances = modele["loaded_instances"]
        if (len(instances) != 1 or instances[0]["id"] != INSTANCE
                or instances[0]["config"]["context_length"] != pipeline.PARAMETRES["context_length"]):
            raise ValueError(f"Charger une seule instance {INSTANCE} avec un contexte de 4 096 tokens.")
        if any(item.get("loaded_instances") for item in reponse["models"] if item["key"] != identifiant):
            raise ValueError("Décharger les autres modèles avant de mesurer le pilote Bonsai.")
        informations = {cle: modele.get(cle) for cle in (
            "key", "publisher", "architecture", "quantization", "selected_variant", "size_bytes", "format",
            "params_string", "max_context_length",
        )}
        return informations, instances[0]


def charger_manifeste(creer=False):
    corpus = pipeline.charger_silver()
    source, meta = pipeline.charger_manifeste(corpus)
    questions = source[:TAILLE]
    if len(questions) != TAILLE or len({question["question_id"] for question in questions}) != TAILLE:
        raise ValueError("Le pilote Bonsai exige 30 identifiants distincts du manifeste Gemma.")
    attendues = [
        {"pilot_order": rang, "question_id": question["question_id"], "seed": meta["seed"]}
        for rang, question in enumerate(questions, 1)
    ]
    if creer and not MANIFESTE.exists():
        DOSSIER.mkdir(parents=True, exist_ok=True)
        pipeline.ecrire_parquet(pd.DataFrame.from_records(attendues), MANIFESTE)
    if pipeline.lire_parquet(MANIFESTE, pipeline.SCHEMA_MANIFESTE) != attendues:
        raise ValueError("Le manifeste Bonsai diffère des 30 premiers rangs du pilote Gemma.")
    return questions, {**meta, "sample_size": TAILLE, "manifest_sha256": pipeline.empreinte_fichier(MANIFESTE)}


def bilan(questions, meta):
    mesures, recus = pipeline.mesures_bilan(questions, meta, STOCKAGE, PROMPTS)
    restantes = {}
    for prompt, mesure in mesures.items():
        deja_mesurees = mesure["tentatives_mesurees"]
        restantes[prompt] = meta["population"] - deja_mesurees
        if deja_mesurees == len(questions):
            mesure["projection_restante_s"] = mesure["duree_active_s"] * restantes[prompt] / deja_mesurees
    terminees = all(mesure["projection_restante_s"] is not None for mesure in mesures.values())
    latences = [latence for reponses in recus.values() for _, _, latence in reponses.values()]
    planifiees = len(PROMPTS) * meta["population"]
    moyenne = mean(latences) if latences else None
    return {
        "population": meta["population"], "sample_size": len(questions), "prompts": mesures,
        "tentatives_restantes": sum(restantes.values()),
        "reponses_recues": len(latences), "latence_moyenne_s": moyenne,
        "extrapolation_inference_complete_s": moyenne * planifiees if moyenne is not None else None,
        "extrapolation_inference_restante_s": moyenne * (planifiees - len(latences))
        if moyenne is not None else None,
        "duree_active_s": sum(mesure["duree_active_s"] for mesure in mesures.values()),
        "projection_complete_s": sum(mesure["projection_complete_s"] for mesure in mesures.values())
        if terminees else None,
        "projection_restante_s": sum(mesure["projection_restante_s"] for mesure in mesures.values())
        if terminees else None,
    }


def main():
    parser = ArgumentParser(description="Pilote Bonsai 27B Q1_0 sur 30 questions du manifeste Gemma.")
    actions = parser.add_subparsers(dest="action", required=True)
    actions.add_parser("manifeste", help="Préparer ou contrôler le manifeste de 30 questions")
    actions.add_parser("bilan", help="Afficher les mesures et projections en lecture seule")
    execution = actions.add_parser("executer", help="Exécuter ou reprendre les 90 inférences du pilote")
    pipeline.ajouter_options_lm_studio(execution)
    execution.set_defaults(model_id=MODELE)
    execution.add_argument("--lms", default="lms")
    args = parser.parse_args()
    try:
        questions, meta = charger_manifeste(creer=args.action != "bilan")
        if args.action == "manifeste":
            print(f"{len(questions)} questions · SHA-256 {meta['manifest_sha256']}")
            return
        if args.action == "executer":
            runtimes = check_output([args.lms, "runtime", "ls"], encoding="utf-8", timeout=15)
            selectionnes = {ligne.split()[0] for ligne in runtimes.splitlines() if "✓" in ligne}
            if args.runtime not in selectionnes:
                raise ValueError(f"Le moteur {args.runtime} doit être sélectionné dans LM Studio.")
            STOCKAGE.bronze.mkdir(parents=True, exist_ok=True)
            pipeline.executer(args, questions, meta, STOCKAGE, PROMPTS, client=LMBonsai(args.url, args.curl))
        print(json.dumps(bilan(questions, meta), indent=2, ensure_ascii=False))
    except (pipeline.ErreurAPI, OSError, RuntimeError, SubprocessError, ValueError) as exc:
        parser.exit(1, f"Erreur : {exc}\n")


if __name__ == "__main__":
    main()
