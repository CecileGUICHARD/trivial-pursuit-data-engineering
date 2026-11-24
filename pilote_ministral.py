from argparse import ArgumentParser
import json
from subprocess import SubprocessError, check_output

import pilote_gemma as pipeline
from pilote_qwen import MOTEUR, PROMPTS, charger_manifeste


MODELE = "mistralai/ministral-3-3b"
VARIANTE = f"{MODELE}@q4_k_m"
INSTANCE = "ministral-benchmark-lot4"
DOSSIER = pipeline.SILVER.parent / "pilote_ministral"
STOCKAGE = pipeline.StockageInference(
    DOSSIER / "pilot.duckdb", pipeline.BRONZE.parent / DOSSIER.name, DOSSIER, "ministral"
)


class LMMinistral(pipeline.LMStudio):
    # La variante Instruct n’expose aucun réglage de réflexion dans LM Studio.
    parametres = {cle: valeur for cle, valeur in pipeline.PARAMETRES.items() if cle != "reasoning"}

    def choisir_modele(self, identifiant):
        reponse, _ = self.requete("models")
        modeles = [modele for modele in reponse["models"] if modele["key"] == identifiant]
        if len(modeles) != 1:
            raise ValueError(f"Le modèle {identifiant} doit être disponible dans LM Studio.")
        modele = modeles[0]
        capacites = modele.get("capabilities", {})
        if (modele.get("selected_variant") != VARIANTE or modele.get("format") != "gguf"
                or "reasoning" in capacites):
            raise ValueError("Sélectionner le GGUF Ministral-3-3B-Instruct-2512 Q4_K_M.")
        instances = [instance for item in reponse["models"] for instance in item["loaded_instances"]]
        context_length = self.parametres["context_length"]
        if (len(instances) != 1 or instances != modele["loaded_instances"] or instances[0]["id"] != INSTANCE
                or instances[0]["config"]["context_length"] != context_length):
            raise ValueError(f"Charger uniquement l’instance {INSTANCE} avec un contexte de {context_length} tokens.")
        informations = {cle: modele.get(cle) for cle in (
            "key", "publisher", "architecture", "quantization", "selected_variant", "size_bytes", "format",
            "params_string", "max_context_length", "capabilities",
        )}
        return informations, instances[0]


def bilan(questions, meta):
    mesures, _ = pipeline.mesures_bilan(questions, meta, STOCKAGE, PROMPTS)
    population = meta["population"]
    for mesure in mesures.values():
        mesure["incorrectes"] = mesure["recues"] - mesure["correctes"]
        projection = mesure["projection_complete_s"]
        if projection is not None:
            mesure["projection_restante_s"] = projection * (population - mesure["tentatives_mesurees"]) / population
    resultat = {"population": population, "sample_size": len(questions), "prompts": mesures}
    for cle in ("duree_active_s", "projection_complete_s", "projection_restante_s"):
        valeurs = [mesure[cle] for mesure in mesures.values()]
        resultat[cle] = sum(valeurs) if None not in valeurs else None
    return resultat


def main():
    parser = ArgumentParser(description="Pilote Ministral-3-3B-Instruct-2512 sur les 30 questions Bonsai et Qwen.")
    actions = parser.add_subparsers(dest="action", required=True)
    actions.add_parser("bilan", help="Afficher les mesures et projections en lecture seule")
    execution = actions.add_parser("executer", help="Exécuter ou reprendre les 90 inférences du pilote")
    execution.add_argument("--url", default="http://127.0.0.1:1234")
    execution.add_argument("--curl", default="curl")
    execution.add_argument("--lms", default="lms")
    execution.add_argument("--lm-studio-version", required=True)
    execution.set_defaults(model_id=MODELE, runtime=MOTEUR)
    args = parser.parse_args()
    try:
        questions, meta = charger_manifeste()
        if args.action == "executer":
            runtimes = check_output([args.lms, "runtime", "ls"], encoding="utf-8", timeout=15)
            selectionnes = {ligne.split()[0] for ligne in runtimes.splitlines() if "✓" in ligne}
            if MOTEUR not in selectionnes:
                raise ValueError(f"Le moteur {MOTEUR} doit être sélectionné dans LM Studio.")
            STOCKAGE.bronze.mkdir(parents=True, exist_ok=True)
            STOCKAGE.silver.mkdir(parents=True, exist_ok=True)
            pipeline.executer(args, questions, meta, STOCKAGE, PROMPTS, client=LMMinistral(args.url, args.curl))
        print(json.dumps(bilan(questions, meta), indent=2, ensure_ascii=False))
    except (pipeline.ErreurAPI, OSError, RuntimeError, SubprocessError, ValueError) as exc:
        parser.exit(1, f"Erreur de pilote Ministral ({exc})\n")


if __name__ == "__main__":
    main()
