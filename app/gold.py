from contextlib import closing
from pathlib import Path

import duckdb
import streamlit as st


DATABASE = Path(__file__).resolve().parents[1] / "data" / "trivial_pursuit.duckdb"
MARTS = (
    "mart_performance",
    "mart_prompt_comparison",
    "mart_category",
    "mart_category_gap",
    "mart_difficulty",
    "mart_question_type",
    "mart_question_outcomes",
)

MODELS = {
    "google/gemma-4-e2b": "Gemma 4 E2B",
    "mistralai/ministral-3-3b": "Ministral 3 3B",
}
PROMPTS = {"P1_choices": "P1", "P2_expert": "P2", "P3_expert_advanced": "P3"}
PROMPT_LABELS = {
    "P1_choices": "P1 — Consigne simple",
    "P2_expert": "P2 — Rôle d’expert",
    "P3_expert_advanced": "P3 — Expert et analyse",
}
TYPES = {"all": "Tous types", "multiple": "QCM", "boolean": "Vrai/faux"}
DIFFICULTIES = {"easy": "Facile", "medium": "Intermédiaire", "hard": "Difficile"}
OUTCOMES = {
    "all_correct": "Réussies par les six",
    "all_incorrect": "Ratées par les six",
    "mixed": "Résultats mixtes",
}


@st.cache_data(show_spinner=False)
def read_marts(path: Path, revision: tuple[int, int]):
    """Read the seven published relations. The file revision invalidates the cache."""
    with closing(duckdb.connect(str(path), read_only=True)) as connection:
        return {name: connection.execute(f"select * from gold.{name}").fetchdf() for name in MARTS}


def load_marts():
    stat = DATABASE.stat()
    return read_marts(DATABASE, (stat.st_mtime_ns, stat.st_size))


def options(frame, column, labels=None):
    values = set(frame[column].dropna())
    if labels is None:
        return sorted(values)
    return [value for value in labels if value in values] + sorted(values.difference(labels))


def config_labels(frame):
    return frame.assign(
        Modèle=frame.model_id.replace(MODELS),
        Prompt=frame.prompt_id.replace(PROMPTS),
    )


def pair_label(pair):
    before, after = pair
    return f"{PROMPTS.get(after, after)} − {PROMPTS.get(before, before)}"


def number(value, digits=0):
    return f"{value:,.{digits}f}".replace(",", "\u202f").replace(".", ",").replace("-", "−")
