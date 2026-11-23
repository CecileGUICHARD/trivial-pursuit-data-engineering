
import pandas as pd

# Charger les données
df = pd.read_csv("data/bronze/questions_raw.csv")

# 1. Volumétrie
print("\n--- VOLUMÉTRIE ---")
print(f"Nombre de questions : {len(df)}")

# 2. Structure
print("\n--- STRUCTURE ---")
print(df.info())

# 3. Complétude
print("\n--- VALEURS MANQUANTES ---")
print(df.isnull().sum())

# 4. Répartition
print("\n--- CATÉGORIES ---")
print(df["category"].value_counts())

print("\n--- DIFFICULTÉS ---")
print(df["difficulty"].value_counts())

print("\n--- TYPES DE QUESTIONS ---")
print(df["type"].value_counts())

# 5. Doublons
print("\n--- DOUBLONS ---")
print(f"Questions dupliquées : {df.duplicated(subset=['question']).sum()}")

print("\n--- ANALYSE DES DOUBLONS ---")

# Afficher toutes les occurrences des questions répétées
doublons = df[df.duplicated(
    subset=["question"], keep=False
)]

print(doublons.to_string(index=False))

# Vérifier si les lignes sont totalement identiques
print("\nDoublons sur toutes les colonnes :")
print(df.duplicated().sum())
