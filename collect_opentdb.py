
import requests
import pandas as pd
import json
from pathlib import Path

# 1. Définir l'API et le dossier de destination
url = "https://opentdb.com/api.php"
params = {"amount": 50}

output = Path("data/bronze")
output.mkdir(parents=True, exist_ok=True)

# 2. Interroger l'API
response = requests.get(url, params=params, timeout=30)
response.raise_for_status()

# 3. Récupérer les données JSON
data = response.json()

if data["response_code"] != 0:
    raise Exception(f"Erreur API : {data['response_code']}")

# 4. Transformer les questions en DataFrame
df = pd.DataFrame(data["results"])

# 5. Conserver les listes de réponses en JSON
df["incorrect_answers"] = df["incorrect_answers"].apply(
    lambda x: json.dumps(x, ensure_ascii=False)
)

# 6. Exporter les données en CSV
df.to_csv(output / "questions_raw.csv",
          index=False,
          encoding="utf-8-sig")

print(f"{len(df)} questions récupérées avec succès.")
