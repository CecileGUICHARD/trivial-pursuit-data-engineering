
import csv
import json
import shutil
import time
from pathlib import Path

import requests

BASE_URL = "https://opentdb.com"
BRONZE = Path(__file__).resolve().parent / "data" / "bronze"
BRONZE.mkdir(parents=True, exist_ok=True)

CSV_PATH = BRONZE / "questions_raw.csv"
STATE_PATH = BRONZE / "collection_state.json"

FIELDS = [
    "type", "difficulty", "category", "question",
    "correct_answer", "incorrect_answers"
]

last_call = 0.0


def get_json(endpoint, params=None):
    global last_call

    for attempt in range(5):
        pause = max(0, 5.3 - (time.monotonic() - last_call))
        if pause:
            time.sleep(pause)

        last_call = time.monotonic()

        try:
            response = requests.get(
                BASE_URL + endpoint,
                params=params,
                timeout=30
            )

            if response.status_code == 429:
                print("Limite HTTP atteinte, nouvelle tentative...")
                continue

            response.raise_for_status()
            return response.json()

        except (requests.RequestException, ValueError) as exc:
            print(f"Erreur reseau ({attempt + 1}/5) : {exc}")

    raise RuntimeError("API inaccessible apres 5 tentatives")


def save_state(state):
    temp = STATE_PATH.with_suffix(".tmp")
    temp.write_text(
        json.dumps(state, indent=2),
        encoding="utf-8"
    )
    temp.replace(STATE_PATH)


def append_questions(questions):
    with CSV_PATH.open("a", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)

        for item in questions:
            row = {name: item[name] for name in FIELDS}
            row["incorrect_answers"] = json.dumps(
                row["incorrect_answers"],
                ensure_ascii=False
            )
            writer.writerow(row)


def main():
    # Recuperer les statistiques de l'API
    stats = get_json("/api_count_global.php")
    counts = stats["categories"]

    expected = stats["overall"][
        "total_num_of_verified_questions"
    ]

    print(f"Questions verifiees annoncees : {expected}")

    # Reprendre une collecte ou en demarrer une nouvelle
    if STATE_PATH.exists():
        if not CSV_PATH.exists():
            raise RuntimeError(
                "Fichier CSV absent : verifier les fichiers de reprise"
            )

        state = json.loads(
            STATE_PATH.read_text(encoding="utf-8")
        )
        print("Reprise de la collecte precedente")

    else:
        # Sauvegarder le CSV du premier test
        if CSV_PATH.exists():
            backup = BRONZE / "questions_test_50.csv"

            if backup.exists():
                raise RuntimeError(
                    "Une sauvegarde existe deja : verifier les CSV"
                )

            shutil.copy2(CSV_PATH, backup)
            CSV_PATH.unlink()

            print("Echantillon de 50 questions sauvegarde")

        # Obtenir un jeton de session
        token_data = get_json(
            "/api_token.php",
            {"command": "request"}
        )

        if token_data.get("response_code") != 0:
            raise RuntimeError("Impossible d'obtenir un jeton")

        state = {
            "token": token_data["token"],
            "counts": {}
        }

        # Creer le CSV avec ses colonnes
        with CSV_PATH.open(
            "w", encoding="utf-8-sig", newline=""
        ) as file:
            csv.DictWriter(
                file, fieldnames=FIELDS
            ).writeheader()

        save_state(state)

    # Collecter chaque categorie
    for category_id, metrics in counts.items():
        target = metrics["total_num_of_verified_questions"]
        done = state["counts"].get(category_id, 0)

        print(f"Categorie {category_id} : {done}/{target}")

        while done < target:
            requested = min(50, target - done)
            rate_errors = 0
            exhausted = False

            while True:
                data = get_json(
                    "/api.php",
                    {
                        "amount": requested,
                        "category": category_id,
                        "token": state["token"]
                    }
                )

                code = data.get("response_code")

                if code == 0:
                    questions = data["results"]
                    append_questions(questions)

                    done += len(questions)
                    state["counts"][category_id] = done
                    save_state(state)

                    print(f"  {done}/{target}")
                    break

                if code == 1 and requested > 1:
                    requested = max(1, requested // 2)
                    print(f"  Lot reduit a {requested}")
                    continue

                if code == 5 and rate_errors < 5:
                    rate_errors += 1
                    print("  Limite de debit, nouvel essai")
                    continue

                if code == 3:
                    raise RuntimeError(
                        "Jeton expire. CSV partiel conserve. "
                        "Verifier la reprise avant de continuer."
                    )

                if code in (1, 4):
                    print(
                        f"  Plus de questions disponibles (code {code})"
                    )
                    exhausted = True
                    break

                raise RuntimeError(
                    f"Erreur API inattendue : {data}"
                )

            if exhausted:
                break

    total = sum(state["counts"].values())

    print(f"\nCollecte terminee : {total} lignes")
    print(f"CSV : {CSV_PATH}")
    print(f"Nombre de reference : {expected}")

    if total != expected:
        print(
            "Ecart a analyser entre le CSV et le compteur API"
        )


if __name__ == "__main__":
    main()
