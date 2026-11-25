import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from charts import (
    AMBER, GRAY, GREEN, MODEL_COLORS, NAVY, ORANGE, RED, TEAL,
    connected_categories, counts_bars, horizontal_bars, model_bars, show, success_with_chance,
)
from gold import DIFFICULTIES, MODELS, OUTCOMES, PROMPT_LABELS, PROMPTS, TYPES, config_labels, number, options, pair_label
from presentation import cards, filter_key, reset_button, takeaway


MULTI_SELECT_HELP = "Tu peux sélectionner plusieurs boutons."


def segments(container, frame, column, title, prefix, labels):
    values = options(frame, column, labels)
    return container.segmented_control(
        title, values, selection_mode="multi", default=values, key=filter_key(prefix, column),
        format_func=lambda value: labels.get(value, value),
        help=MULTI_SELECT_HELP if len(values) > 1 else None,
    )


def category_filter(container, frame, prefix):
    choices = options(frame, "category")
    selected = container.multiselect(
        "Catégories", choices, placeholder="Toutes les catégories", key=filter_key(prefix, "category"), wrap=True,
    )
    return selected or choices


def configurations(frame, prefix):
    model_filter, prompt_filter, reset = st.columns([1.05, 2.45, .72], vertical_alignment="bottom")
    models = segments(model_filter, frame, "model_id", "Modèles", prefix, MODELS)
    prompts = segments(prompt_filter, frame, "prompt_id", "Consignes données aux IA", prefix, PROMPT_LABELS)
    reset_button(reset, prefix)
    return frame.loc[frame.prompt_id.isin(prompts) & frame.model_id.isin(models)]


def configuration_cards(data, key, definitions, dimension="Prompt"):
    items = []
    for title, field, preference, digits, unit in definitions:
        values = data[field]
        best = values.min() if preference == "min" else values.max()
        leaders = data.loc[values.eq(best)]
        lead = leaders.iloc[0]
        context = f"{lead['Modèle']} · {lead[dimension]}"
        if len(leaders) > 1:
            context += f" · {len(leaders)} ex æquo"
        items.append((title, f"{number(best, digits)} {unit}", context))
    cards(key, items)


def empty(frame):
    if frame.empty:
        st.info("Aucun résultat pour ces filtres.")
    return frame.empty


def configuration_axis(fig, models, prompts, labels):
    short = models.str.split().str[0]
    fig.update_xaxes(tickmode="array", tickvals=labels, ticktext=short + "<br>" + prompts, tickangle=0)


def performance(frame):
    data = config_labels(configurations(frame, "performance"))
    if empty(data):
        return
    data = data.sort_values(["Modèle", "Prompt"])
    configuration_cards(data, "duel", [
        ("Meilleur taux de bonnes réponses", "correct_pct", "max", 2, "%"),
        ("Meilleure conformité", "compliance_pct", "max", 2, "%"),
        ("Temps moyen de réponse le plus court", "avg_response_time_s", "min", 3, "s"),
    ])
    best = data.loc[data.correct_pct.idxmax()]
    takeaway("duel", f"**{best['Modèle']} · {best.Prompt}** obtient {number(best.correct_count)} bonnes réponses sur {number(best.response_count)}. La conformité indique si la réponse respecte le format demandé.")
    precision, compliance = st.columns(2)
    with precision:
        st.subheader("Taux de bonnes réponses")
        show(model_bars(data, "Prompt", "correct_pct", "%"), "global_accuracy")
    with compliance:
        st.subheader("Conformité")
        show(model_bars(data, "Prompt", "compliance_pct", "%"), "global_compliance")
    latency, distribution = st.columns(2)
    with latency:
        st.subheader("Temps moyen de réponse")
        show(model_bars(data, "Prompt", "avg_response_time_s", "s"), "global_latency")
    with distribution:
        st.subheader("Répartition des réponses")
        labels = data["Modèle"] + " · " + data.Prompt
        fig = go.Figure()
        for field, label, color in (
            ("correct_pct", "Correctes", GREEN),
            ("incorrect_conforming_pct", "Incorrectes conformes", AMBER),
            ("out_of_format_pct", "Hors format", RED),
        ):
            fig.add_bar(
                x=labels, y=data[field], name=label, marker_color=color,
                hovertemplate="%{x}<br>%{y:.2f} %<extra>%{fullData.name}</extra>",
            )
        fig.update_layout(barmode="stack")
        configuration_axis(fig, data["Modèle"], data.Prompt, labels)
        fig.update_yaxes(title_text="%", range=[0, 100], ticksuffix=" %")
        show(fig, "global_distribution", height=285)


def prompt_comparison(frame):
    model_filter, pair_filter, reset = st.columns([1, 1.5, .65], vertical_alignment="bottom")
    models = segments(model_filter, frame, "model_id", "Modèles", "comparison", MODELS)
    pairs = sorted(set(zip(frame.prompt_from, frame.prompt_to, strict=True)), key=lambda pair: (pair[1], pair[0]))
    kept = pair_filter.segmented_control(
        "Évolution de la consigne", pairs, selection_mode="multi", default=pairs,
        format_func=pair_label, key=filter_key("comparison", "pairs"),
        help=MULTI_SELECT_HELP if len(pairs) > 1 else None,
    )
    reset_button(reset, "comparison")
    st.caption(" · ".join(PROMPT_LABELS.values()) + ". De 50 % à 55 %, l’écart est de 5 points de pourcentage (pp).")
    oriented = list(zip(frame.prompt_from, frame.prompt_to, strict=True))
    data = frame.loc[frame.model_id.isin(models) & pd.Series([pair in kept for pair in oriented], index=frame.index)]
    if empty(data):
        return
    data = data.assign(Modèle=data.model_id.replace(MODELS), Paire=[pair_label(pair) for pair in zip(data.prompt_from, data.prompt_to, strict=True)])
    data = data.sort_values(["Paire", "Modèle"])
    best_change = data.success_delta_pp.max()
    if best_change > 0:
        change_label = "Plus forte hausse du taux de bonnes réponses"
    elif best_change < 0:
        change_label = "Plus faible baisse du taux de bonnes réponses"
    else:
        change_label = "Taux de bonnes réponses inchangé"
    configuration_cards(data, "prompts", [
        (change_label, "success_delta_pp", "max", 2, "pts"),
        ("Meilleur écart de conformité", "compliance_delta_pp", "max", 2, "pts"),
        ("Plus faible écart de temps de réponse", "response_time_delta_s", "min", 3, "s"),
    ], dimension="Paire")
    example = data.loc[data.success_delta_pp.abs().idxmax()]
    takeaway("prompts", f"Le changement de taux de bonnes réponses le plus marqué est de **{number(example.success_delta_pp, 2)} points** pour **{example['Modèle']} · {example.Paire}**. {number(example.gain_count)} réponses deviennent justes et {number(example.loss_count)} deviennent fausses.")
    transitions, accuracy = st.columns(2)
    with transitions:
        st.subheader("Gains et pertes")
        labels = data["Modèle"] + " · " + data.Paire
        fig = go.Figure()
        fig.add_bar(x=labels, y=data.gain_count, name="Gains", marker_color=GREEN,
                    texttemplate="%{y:,d}", textposition="outside", cliponaxis=False,
                    hovertemplate="%{x}<br>%{y:,d} gains<extra></extra>")
        fig.add_bar(x=labels, y=-data.loss_count, name="Pertes", marker_color=AMBER, customdata=data.loss_count,
                    texttemplate="%{y:,d}", textposition="outside", cliponaxis=False,
                    hovertemplate="%{x}<br>%{customdata:,d} pertes<extra></extra>")
        fig.update_layout(barmode="relative")
        configuration_axis(fig, data["Modèle"], data.Paire, labels)
        fig.update_yaxes(
            title_text="Questions", zeroline=True, zerolinecolor=GRAY,
            range=[-max(1, data.loss_count.max() * 1.16), max(1, data.gain_count.max() * 1.20)],
        )
        show(fig, "prompt_transitions")
    with accuracy:
        st.subheader("Écart du taux de bonnes réponses")
        show(model_bars(data, "Paire", "success_delta_pp", "pp"), "prompt_accuracy")
    compliance, latency = st.columns(2)
    with compliance:
        st.subheader("Écart de conformité")
        show(model_bars(data, "Paire", "compliance_delta_pp", "pp"), "prompt_compliance")
    with latency:
        st.subheader("Écart du temps moyen de réponse")
        show(model_bars(data, "Paire", "response_time_delta_s", "s"), "prompt_latency")

    columns = {
        "success_from_pct": "Taux de bonnes réponses avant", "success_to_pct": "Taux de bonnes réponses après",
        "compliance_from_pct": "Conformité avant", "compliance_to_pct": "Conformité après",
        "avg_response_time_from_s": "Temps moyen de réponse avant", "avg_response_time_to_s": "Temps moyen de réponse après",
    }
    table = data[["Modèle", "Paire", *columns]].copy()
    for column in columns:
        digits, suffix = (2, " %") if column.endswith("_pct") else (3, " s")
        table[column] = table[column].map(lambda value: number(value, digits) + suffix)
    with st.expander("Ouvrir le tableau des mesures avant et après"):
        st.caption("Chaque écart compare le prompt d’arrivée au prompt de départ sur les mêmes questions.")
        st.dataframe(table.rename(columns=columns), hide_index=True, width="stretch")


def categories(frame):
    selected = configurations(frame, "category")
    categories = category_filter(st, frame, "category")
    data = config_labels(selected.loc[selected.category.isin(categories)])
    if empty(data):
        return
    items = []
    for model, rows in data.groupby("Modèle", sort=True):
        leader = rows.loc[rows.success_pct.idxmax()]
        items.append((f"Meilleur score · {model}", f"{number(leader.success_pct, 2)} %", f"{leader.category} · {leader.Prompt}"))
    cards("categories", items)
    example = data.loc[data.success_pct.idxmax()]
    takeaway("categories", f"Dans cette sélection, **{example['Modèle']} · {example.Prompt}** répond juste à {number(example.correct_count)} questions sur {number(example.response_count)} en **{example.category}**. La carte thermique permet de suivre cette catégorie d’une consigne à l’autre.")
    rankings, heatmaps = st.tabs(["Classement", "Carte thermique"])
    with rankings:
        ranks = data.groupby(["Modèle", "Prompt"], sort=True)
        slots = st.columns(min(2, ranks.ngroups))
        for index, ((model, prompt), rows) in enumerate(ranks):
            with slots[index % len(slots)]:
                st.subheader(f"{model} · {prompt}")
                rows = rows.sort_values(["success_pct", "category"], ascending=[False, True])
                fig = horizontal_bars(
                    rows, "success_pct", "category", MODEL_COLORS.get(model, TEAL), "Réussite (%)",
                    "%{y}<br>%{x:.2f} % de réussite<br>%{customdata:,d} réponses<extra></extra>",
                    customdata=rows.response_count,
                )
                fig.update_xaxes(range=[0, 100], ticksuffix=" %")
                show(fig, f"category_rank_{index}", height=max(220, 77 + 21 * len(rows)))
    with heatmaps:
        slots = st.columns(min(2, data["Modèle"].nunique()))
        for index, (model, rows) in enumerate(data.groupby("Modèle", sort=True)):
            with slots[index % len(slots)]:
                st.subheader(model)
                values = rows.pivot(index="category", columns="Prompt", values="success_pct")
                heat_end = "#ffd1a8" if MODEL_COLORS.get(model) == ORANGE else "#86d3c6"
                fig = go.Figure(go.Heatmap(
                    x=values.columns, y=values.index, z=values.to_numpy(), zmin=0, zmax=100,
                    colorscale=[[0, "#f7fafb"], [1, heat_end]], xgap=2, ygap=2,
                    colorbar=dict(title="%", thickness=12),
                    texttemplate="%{z:.2f} %", textfont=dict(color=NAVY, size=11),
                    hovertemplate="%{y} · %{x}<br>%{z:.2f} % de réussite<extra></extra>",
                ))
                fig.update_yaxes(autorange="reversed")
                show(fig, f"category_heatmap_{index}", height=max(220, 77 + 21 * len(values)))


def category_gaps(frame):
    prompt_filter, categories_filter, reset = st.columns([2.15, 1.6, .68], vertical_alignment="bottom")
    prompts = segments(prompt_filter, frame, "prompt_id", "Consignes données aux IA", "gap", PROMPT_LABELS)
    categories = category_filter(categories_filter, frame, "gap")
    reset_button(reset, "gap")
    data = frame.loc[frame.prompt_id.isin(prompts) & frame.category.isin(categories)]
    if empty(data):
        return
    biggest = data.loc[data.success_gap_pp.abs().idxmax()]
    cards("gaps", [
        ("Gemma", f"{number(biggest.gemma_success_pct, 2)} %", biggest.category),
        ("Ministral", f"{number(biggest.ministral_success_pct, 2)} %", biggest.category),
        ("Écart Gemma − Ministral", f"{number(biggest.success_gap_pp, 2)} pts", PROMPTS[biggest.prompt_id]),
    ])
    takeaway("gaps", f"L’écart le plus marqué de cette sélection se trouve dans **{biggest.category} · {PROMPTS[biggest.prompt_id]}**. Plus les deux points sont éloignés, plus les taux de réussite diffèrent.")
    limit = max(1.0, data.success_gap_pp.abs().max()) * 1.1
    groups = data.groupby("prompt_id", sort=True)
    points, bars = st.tabs(["Comparaison à points reliés", "Écarts en points"])
    with points:
        slots = st.columns(min(2, groups.ngroups))
        for index, (prompt, rows) in enumerate(groups):
            with slots[index % len(slots)]:
                st.subheader(PROMPT_LABELS[prompt])
                rows = rows.sort_values(["success_gap_pp", "category"], ascending=[False, True])
                show(connected_categories(rows), f"category_connected_{index}", height=max(245, 100 + 22 * len(rows)))
    with bars:
        st.caption("Un écart positif favorise Gemma, un écart négatif favorise Ministral. Le point gris signale une égalité.")
        slots = st.columns(min(2, groups.ngroups))
        for index, (prompt, rows) in enumerate(groups):
            with slots[index % len(slots)]:
                st.subheader(PROMPT_LABELS[prompt])
                rows = rows.sort_values(["success_gap_pp", "category"], ascending=[False, True])
                colors = [GRAY if tie else TEAL if gap > 0 else ORANGE for tie, gap in zip(rows.is_tie, rows.success_gap_pp, strict=True)]
                fig = horizontal_bars(
                    rows, "success_gap_pp", "category", colors, "Écart (pp)",
                    "%{y}<br>Écart %{x:+.2f} pp<br>Gemma %{customdata[0]:.2f} %<br>Ministral %{customdata[1]:.2f} %<extra></extra>",
                    customdata=rows[["gemma_success_pct", "ministral_success_pct"]].to_numpy(),
                )
                ties = rows.loc[rows.is_tie]
                if not ties.empty:
                    fig.add_scatter(
                        x=ties.success_gap_pp, y=ties.category, mode="markers", name="Égalité", showlegend=False,
                        marker=dict(color=GRAY, size=8), customdata=ties[["gemma_success_pct", "ministral_success_pct"]].to_numpy(),
                        hovertemplate="%{y}<br>Égalité<br>Gemma %{customdata[0]:.2f} %<br>Ministral %{customdata[1]:.2f} %<extra></extra>",
                    )
                fig.update_xaxes(range=[-limit, limit])
                show(fig, f"category_gap_{index}", height=max(220, 77 + 21 * len(rows)))


def difficulty(frame):
    selected = configurations(frame, "difficulty")
    left, right = st.columns(2)
    levels = segments(left, frame, "difficulty", "Difficultés", "difficulty", DIFFICULTIES)
    question_type = right.segmented_control(
        "Type de question", options(frame, "type", TYPES), format_func=TYPES.get, default="all",
        required=True, key=filter_key("difficulty", "type"),
    )
    data = config_labels(selected.loc[selected.difficulty.isin(levels) & selected.type.eq(question_type)])
    if empty(data):
        return
    data = data.assign(Difficulté=data.difficulty.replace(DIFFICULTIES))
    best = data.loc[data.above_chance_pp.idxmax()]
    cards("difficulty", [("Plus grand écart au hasard", f"{number(best.above_chance_pp, 2)} pts", f"{best['Modèle']} · {best.Prompt} · {best['Difficulté']}")])
    references = data[["difficulty", "chance_pct"]].drop_duplicates().set_index("difficulty").chance_pct
    if question_type == "all":
        chance = " · ".join(f"{DIFFICULTIES[level]} {number(references[level], 2)} %" for level in DIFFICULTIES if level in references)
        takeaway("difficulty", f"**Score au hasard, repère gris.** Il suit la répartition des QCM et des vrai/faux dans chaque difficulté. {chance}.")
    else:
        takeaway("difficulty", f"**Score au hasard, repère gris.** Une réponse tirée au sort donne {number(references.iloc[0], 2)} % de bonnes réponses pour ce type de question.")
    st.subheader("Réussite et référence du hasard")
    order = list(DIFFICULTIES.values())
    show(success_with_chance(data, "Difficulté", order), "difficulty_success", height=320)
    st.subheader("Écart au hasard")
    show(model_bars(data, "Difficulté", "above_chance_pp", "pp", facet=True, order=order), "difficulty_above_chance", height=310)


def question_types(frame):
    selected = configurations(frame, "type")
    types = segments(st, frame, "type", "Types de questions", "type", TYPES)
    data = config_labels(selected.loc[selected.type.isin(types)])
    if empty(data):
        return
    data = data.assign(Type=data.type.replace(TYPES))
    order = [TYPES[value] for value in types]
    best = data.loc[data.above_chance_pp.idxmax()]
    cards("types", [("Plus grand écart au hasard", f"{number(best.above_chance_pp, 2)} pts", f"{best['Modèle']} · {best.Prompt} · {best.Type}")])
    example = data.loc[data.above_chance_pp.idxmin()]
    takeaway("types", f"**Score au hasard, repère gris.** Tirer une réponse au sort donne 1 chance sur 4 en QCM (25 %) et 1 chance sur 2 en vrai/faux (50 %). Ici, **{example['Modèle']} · {example.Prompt}** obtient {number(example.success_pct, 2)} % en {example.Type.lower()}, pour un repère de {number(example.chance_pct, 2)} %.")
    st.subheader("Réussite et référence du hasard")
    show(success_with_chance(data, "Type", order), "type_success", height=320)
    st.subheader("Écart au hasard")
    show(model_bars(data, "Type", "above_chance_pp", "pp", facet=True, order=order), "type_above_chance", height=310)
    st.subheader("Conformité")
    show(model_bars(data, "Type", "compliance_pct", "%", facet=True, order=order), "type_compliance", height=310)


def question_outcomes(frame):
    categories_filter, level_filter, type_filter, reset = st.columns([1.1, 1.15, 1, .65], vertical_alignment="bottom")
    categories = category_filter(categories_filter, frame, "outcomes")
    levels = segments(level_filter, frame, "difficulty", "Difficultés", "outcomes", DIFFICULTIES)
    types = segments(type_filter, frame, "type", "Types de questions", "outcomes", TYPES)
    reset_button(reset, "outcomes", "details")
    data = frame.loc[frame.category.isin(categories) & frame.difficulty.isin(levels) & frame.type.isin(types)]
    if empty(data):
        clear_reveal()
        st.write("**0** question correspondant aux filtres du tableau")
        return

    totals = data.outcome.value_counts().reindex(OUTCOMES, fill_value=0)
    failures = data.loc[data.outcome.eq("all_incorrect")]
    consensus = failures.loc[failures.unanimous_wrong]
    cards("outcomes", [(title, number(value), None) for title, value in zip(
        [*OUTCOMES.values(), "Dont consensus incorrects"], [*totals, len(consensus)], strict=True,
    )])
    if failures.empty:
        takeaway("outcomes", "Les six configurations n’échouent ensemble sur aucune des questions de la sélection.")
    else:
        takeaway("outcomes", f"Sur **{number(len(failures))} échecs communs**, les six configurations donnent **{number(len(consensus))} fois** la même réponse fausse au format attendu.")

    question_details(frame, data)

    outcomes, shared, by_type = st.columns(3)
    with outcomes:
        st.subheader("Résultats sur les six configurations")
        show(counts_bars(list(OUTCOMES.values()), totals, [GREEN, RED, NAVY]), "outcomes_distribution", height=285)
    with shared:
        st.subheader("Échecs communs")
        show(counts_bars(["Consensus incorrects", "Autres échecs"], [len(consensus), len(failures) - len(consensus)], [AMBER, RED]), "outcomes_shared", height=285)
        if failures.empty:
            st.caption("Part des consensus indisponible pour cette sélection sans échec commun.")
        else:
            st.caption(f"Part des consensus parmi les échecs communs · **{number(100 * len(consensus) / len(failures), 2)} %**")
    with by_type:
        st.subheader("Consensus incorrects par type")
        type_values = ["multiple", "boolean"]
        counts = consensus.type.value_counts().reindex(type_values, fill_value=0)
        show(counts_bars([TYPES[value] for value in type_values], counts, [AMBER, AMBER]), "outcomes_consensus_type", height=285)


def question_details(frame, data):
    st.subheader("Explorer les questions")
    search_filter, outcome_filter, consensus_filter = st.columns([1.1, 1.5, .8])
    search = search_filter.text_input("Rechercher dans les questions", placeholder="Un mot ou une expression", key=filter_key("details", "search")).strip()
    outcomes = segments(outcome_filter, frame, "outcome", "Résultats", "details", OUTCOMES)
    flag = consensus_filter.segmented_control(
        "Consensus incorrect", ["Tous", "Oui", "Non"], default="Tous", required=True, key=filter_key("details", "consensus"),
    )
    details = data.loc[data.outcome.isin(outcomes) & data.question.str.contains(search, case=False, regex=False, na=False)]
    if flag != "Tous":
        details = details.loc[details.unanimous_wrong.eq(flag == "Oui")]
    st.write(f"**{number(len(details))}** question(s) correspondant aux filtres du tableau")
    if empty(details):
        clear_reveal()
        return
    details = details.sort_values(["category", "question", "question_id"])
    question_card(details)
    with st.expander("Ouvrir le tableau détaillé des questions"):
        st.caption("La réponse commune utilise le format du benchmark (lettre, True ou False). Le consensus incorrect fait partie des échecs communs.")
        question_table(details)


def clear_reveal():
    st.session_state.pop("filter_details_revealed", None)


def toggle_reveal(question_id):
    if st.session_state.get("filter_details_revealed") == question_id:
        clear_reveal()
    else:
        st.session_state["filter_details_revealed"] = question_id


def question_card(details):
    questions = details.set_index("question_id")
    with st.container(key="question_explorer", border=True):
        st.subheader("À toi de jouer")
        question_id = st.selectbox(
            "Choisir une question", questions.index, key=filter_key("details", "question_id"),
            format_func=lambda value: questions.at[value, "question"],
        )
        if st.session_state.get("filter_details_current_question") != question_id:
            clear_reveal()
            st.session_state["filter_details_current_question"] = question_id
        row = questions.loc[question_id]
        st.caption(f"{row.category} · {DIFFICULTIES[row.difficulty]} · {TYPES[row.type]}")
        st.write(f"**{row.question}**")
        choices = zip("ABCD", row.answer_choices, strict=True) if row.type == "multiple" else (("", choice) for choice in row.answer_choices)
        slots = st.columns(2)
        for index, (label, choice) in enumerate(choices):
            with slots[index % len(slots)].container(key=f"quiz_choice_{index}", border=True):
                st.write(f"**{label}** · {choice}" if label else choice)
        revealed = st.session_state.get("filter_details_revealed") == question_id
        st.button(
            "Masquer la réponse" if revealed else "Révéler la réponse", type="primary",
            key="reveal_question", on_click=toggle_reveal, args=(question_id,),
        )
        if revealed:
            st.success(f"Bonne réponse · **{row.correct_answer}** (réponse attendue **{row.expected_answer}**).")
            if row.unanimous_wrong:
                st.info(f"Consensus incorrect · les six configurations ont répondu **{row.same_wrong_answer}**.")


def question_table(details):
    labels = {
        "question": "Question", "category": "Catégorie", "difficulty": "Difficulté", "type": "Type",
        "correct_answer": "Bonne réponse", "answer_choices": "Choix présentés", "expected_answer": "Réponse attendue",
        "same_wrong_answer": "Réponse commune", "outcome": "Résultat", "unanimous_wrong": "Consensus incorrect",
    }
    table = details[list(labels)].copy()
    table = table.assign(
        difficulty=table.difficulty.replace(DIFFICULTIES), type=table.type.replace(TYPES), outcome=table.outcome.replace(OUTCOMES),
    )
    columns = {field: st.column_config.TextColumn(label) for field, label in labels.items()}
    columns["question"] = st.column_config.TextColumn(labels["question"], width="large")
    columns["answer_choices"] = st.column_config.ListColumn(labels["answer_choices"], width="large")
    columns["unanimous_wrong"] = st.column_config.CheckboxColumn(labels["unanimous_wrong"])
    st.dataframe(table, hide_index=True, column_config=columns, height=390, width="stretch")
