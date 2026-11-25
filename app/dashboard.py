import duckdb
import streamlit as st

from gold import load_marts
from presentation import TITLE, intro, welcome
from views import categories, category_gaps, difficulty, performance, prompt_comparison, question_outcomes, question_types


def main():
    st.set_page_config(page_title=TITLE, layout="wide")
    welcome()

    try:
        marts = load_marts()
    except (OSError, duckdb.Error):
        st.error("La base Gold est indisponible. Vérifiez `data/trivial_pursuit.duckdb` et suivez la reconstruction décrite dans le README.")
        st.stop()

    performance_tab, prompt_tab, knowledge_tab, outcomes_tab = st.tabs([
        "Le duel des IA", "Le pouvoir des prompts", "Les domaines de prédilection", "Les questions pièges",
    ])
    with performance_tab:
        intro("Quelle IA répond le mieux ?", "Compare Gemma et Ministral sur la justesse des réponses, le respect du format et la vitesse.")
        performance(marts["mart_performance"])
    with prompt_tab:
        intro("La consigne fait-elle la différence ?", "Sur les mêmes questions, observe ce que chaque modèle gagne ou perd quand on change sa consigne.")
        prompt_comparison(marts["mart_prompt_comparison"])
    with knowledge_tab:
        intro("Dans quels domaines chaque IA excelle-t-elle ?", "Explore les catégories ou compare les résultats selon la difficulté et le type de question.")
        gap_tab, category_tab, difficulty_tab, type_tab = st.tabs([
            "Écarts entre modèles", "Performance par catégorie", "Difficulté", "Type de question",
        ])
        with category_tab:
            categories(marts["mart_category"])
        with gap_tab:
            category_gaps(marts["mart_category_gap"])
        with difficulty_tab:
            difficulty(marts["mart_difficulty"])
        with type_tab:
            question_types(marts["mart_question_type"])
    with outcomes_tab:
        intro(
            "Quelles questions piègent les deux IA ?",
            "Chaque question a été posée aux deux modèles, chacun avec les trois consignes. "
            "Ce sont les six configurations du benchmark. Essaie de répondre avant de révéler la solution.",
        )
        question_outcomes(marts["mart_question_outcomes"])


if __name__ == "__main__":
    main()
