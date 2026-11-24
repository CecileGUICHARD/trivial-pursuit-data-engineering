from argparse import ArgumentParser
import json
from subprocess import SubprocessError, check_output

import pilote_bonsai as bonsai
import pilote_gemma as pipeline


MODELE = "qwen/qwen3-4b-2507"
VARIANTE = f"{MODELE}@q4_k_m"
INSTANCE = "qwen-benchmark-lot4"
MOTEUR = "llama.cpp-win-x86_64-vulkan-avx2@2.80.1"
EMPREINTE_MANIFESTE = "79d2d9c59f0aa56b16af8e1b6a9b2583dbc510f2cb0fe9e98cf05a8055e3a560"
PROMPTS = bonsai.PROMPTS
DOSSIER = pipeline.SILVER.parent / "pilote_qwen"
STOCKAGE = pipeline.StockageInference(
    DOSSIER / "pilot.duckdb", pipeline.BRONZE.parent / DOSSIER.name, DOSSIER, "qwen"
)


class LMQwen(pipeline.LMStudio):
    # Instruct 2507 fonctionne uniquement sans mode de réflexion.
    parametres = {cle: valeur for cle, valeur in pipeline.PARAMETRES.items() if cle != "reasoning"}

    def choisir_modele(self, identifiant):
        reponse, _ = self.requete("models")
        modeles = [modele for modele in reponse["models"] if modele["key"] == identifiant]
        if len(modeles) != 1 or modeles[0].get("selected_variant") != VARIANTE:
            raise ValueError(f"La variante {VARIANTE} doit être sélectionnée dans LM Studio.")
        modele = modeles[0]
        instances = modele["loaded_instances"]
        if (len(instances) != 1 or instances[0]["id"] != INSTANCE
                or instances[0]["config"]["context_length"] != self.parametres["context_length"]):
            raise ValueError(f"Charger une seule instance {INSTANCE} avec un contexte de 4 096 tokens.")
        if any(item["loaded_instances"] for item in reponse["models"] if item["key"] != identifiant):
            raise ValueError("Décharger les autres modèles avant de mesurer le pilote Qwen.")
        informations = {cle: modele.get(cle) for cle in (
            "key", "publisher", "architecture", "quantization", "selected_variant", "size_bytes", "format",
            "params_string", "max_context_length", "capabilities",
        )}
        return informations, instances[0]


def charger_manifeste():
    questions, meta = bonsai.charger_manifeste()
    if meta["manifest_sha256"] != EMPREINTE_MANIFESTE:
        raise ValueError("L’empreinte du manifeste Bonsai diffère de celle du pilote historique.")
    return questions, meta


def bilan(questions, meta):
    mesures, _ = pipeline.mesures_bilan(questions, meta, STOCKAGE, PROMPTS)
    restantes = meta["population"] - len(questions)
    for mesure in mesures.values():
        projection = mesure["projection_complete_s"]
        mesure["projection_restante_s"] = (projection * restantes / meta["population"]
                                            if projection is not None else None)
    complet = all(mesure["projection_complete_s"] is not None for mesure in mesures.values())
    resultat = {
        "population": meta["population"],
        "sample_size": len(questions),
        "prompts": mesures,
        "duree_active_s": sum(mesure["duree_active_s"] for mesure in mesures.values()),
    }
    for cle in ("projection_complete_s", "projection_restante_s"):
        resultat[cle] = sum(mesure[cle] for mesure in mesures.values()) if complet else None
    return resultat


def main():
    parser = ArgumentParser(description="Pilote Qwen3-4B-Instruct-2507 Q4_K_M sur les 30 questions Bonsai.")
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
            pipeline.executer(args, questions, meta, STOCKAGE, PROMPTS, client=LMQwen(args.url, args.curl))
        print(json.dumps(bilan(questions, meta), indent=2, ensure_ascii=False))
    except (pipeline.ErreurAPI, OSError, RuntimeError, SubprocessError, ValueError) as exc:
        parser.exit(1, f"Erreur : {exc}\n")


if __name__ == "__main__":
    main()
