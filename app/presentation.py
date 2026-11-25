from pathlib import Path

import streamlit as st


TITLE = "Les intelligences artificielles sont-elles bonnes au Trivial Pursuit ?"


def welcome():
    st.html(Path(__file__).with_name("dashboard.css"))
    heading = TITLE.replace("sont-elles", "<span class='quiz-nowrap'>sont-elles</span>")
    st.html(f"""
    <section class="quiz-hero" aria-labelledby="quiz-title">
      <div class="quiz-hero-copy">
        <p class="quiz-context">Benchmark de culture générale</p>
        <h1 id="quiz-title">{heading}</h1>
        <p class="quiz-description">Deux modèles répondent aux mêmes questions OpenTDB, rédigées à l’origine en anglais.
        Explore leurs réponses, compare leurs points forts et essaie de déjouer les questions pièges.</p>
        <ul class="quiz-facts" role="list" aria-label="Chiffres clés du benchmark">
          <li><strong>5 290</strong> questions</li>
          <li><strong>24</strong> catégories</li>
          <li><strong>31 740</strong> réponses</li>
          <li><strong>2</strong> modèles</li>
          <li><strong>3</strong> prompts</li>
          <li><strong>6</strong> configurations</li>
        </ul>
      </div>
      <div class="quiz-art" aria-hidden="true">
        <span class="quiz-orbit"></span><span class="quiz-wheel"><b>?</b></span>
        <span class="quiz-token quiz-token-teal"></span><span class="quiz-token quiz-token-amber"></span>
      </div>
    </section>
    """)


def intro(question, description):
    st.header(question)
    st.caption(description)


def filter_key(scope, field):
    generation = st.session_state.get(f"filter_generation_{scope}", 0)
    key = f"filter_{scope}_{field}"
    return f"{key}__{generation}" if generation else key


def reset_filters(*scopes):
    prefixes = tuple(f"filter_{scope}_" for scope in scopes)
    for key in list(st.session_state):
        if key.startswith(prefixes):
            del st.session_state[key]
    # A fresh widget identity also resets the selection held by the browser.
    for scope in scopes:
        key = f"filter_generation_{scope}"
        st.session_state[key] = st.session_state.get(key, 0) + 1


def reset_button(container, *scopes):
    key = "reset_" + "_".join(scopes)
    container.button("Réinitialiser les filtres", key=key, on_click=reset_filters, args=scopes)


def cards(key, items):
    """Each card displays a selected Gold figure and the scope it describes."""
    for index, (slot, (label, value, context)) in enumerate(zip(st.columns(len(items)), items, strict=True)):
        with slot.container(key=f"kpi_{key}_{index}", border=True):
            st.metric(label, value)
            if context:
                st.caption(context)


def takeaway(key, text):
    with st.container(key=f"takeaway_{key}"):
        st.markdown(f"**À retenir**  \n{text}")
