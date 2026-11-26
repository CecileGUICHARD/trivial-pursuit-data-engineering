import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from gold import MODELS, PROMPTS


NAVY = "#223858"
# Palette turquoise et orange : trois turquoises, deux oranges, un corail.
TEAL = "#2FB5A3"         # Gemma
TEAL_LIGHT = "#45C9B8"   # résultats mixtes, fin du dégradé Gemma
TEAL_DEEP = "#1E9C8F"    # réponses correctes, gains
ORANGE = "#F59A4F"       # Ministral, consensus incorrects
ORANGE_LIGHT = "#F7B27A" # incorrectes conformes, fin du dégradé Ministral
CORAL = "#EF7F67"        # hors format, pertes, échecs
GREEN, AMBER, RED = TEAL_DEEP, ORANGE_LIGHT, CORAL
GRAY = "#566777"
MODEL_COLORS = dict(zip(MODELS.values(), (TEAL, ORANGE), strict=True))


def show(fig, key, height=285):
    fig.update_layout(
        template="plotly_white",
        height=height,
        margin=dict(l=12, r=16, b=14, t=26),
        font=dict(family="Arial, Liberation Sans, sans-serif", color=NAVY, size=12),
        separators=",\u202f",
        legend=dict(orientation="h", y=-0.21, title_text=""),
        hoverlabel=dict(namelength=-1),
        hovermode="closest",
    )
    fig.update_xaxes(automargin=True, title_standoff=8)
    fig.update_yaxes(automargin=True, title_standoff=8, gridcolor="#e4ecf3")
    st.plotly_chart(fig, key=key, width="stretch", theme=None, config={"displaylogo": False, "responsive": True})


def model_bars(frame, x, y, unit, *, facet=False, order=None):
    orders = {"Prompt": list(PROMPTS.values()), "Modèle": list(MODEL_COLORS)}
    if order is not None:
        orders[x] = order
    fig = px.bar(
        frame, x=x, y=y, color="Modèle",
        facet_col="Prompt" if facet else None, barmode="group", category_orders=orders,
        color_discrete_map=MODEL_COLORS,
        labels={y: unit, x: ""},
    )
    value = {"%": "%{y:.2f} %", "pp": "%{y:+.2f} pp", "s": "%{y:.3f} s"}[unit]
    fig.update_traces(
        texttemplate=value, textposition="outside", textfont_size=11, cliponaxis=False,
        hovertemplate=f"%{{x}}<br>{value}<extra>%{{fullData.name}}</extra>",
    )
    fig.update_xaxes(title=None)
    fig.update_layout(uniformtext_minsize=8, uniformtext_mode="hide")
    if facet:
        fig.for_each_annotation(lambda annotation: annotation.update(text=annotation.text.split("=", 1)[-1]))
    if unit == "%":
        fig.update_yaxes(range=[0, 112], ticksuffix=" %")
    else:
        low, high = min(0, frame[y].min()), max(0, frame[y].max())
        padding = (high - low) * .18 or .2
        fig.update_yaxes(range=[low - (padding if low < 0 else 0), high + padding])
    if unit == "pp":
        fig.update_yaxes(zeroline=True, zerolinecolor=GRAY, zerolinewidth=1)
    return fig


def success_with_chance(frame, dimension, order):
    fig = model_bars(frame, dimension, "success_pct", "%", facet=True, order=order)
    labels = list(PROMPTS.values())
    prompts = sorted(frame.Prompt.unique(), key=lambda prompt: (prompt not in labels, labels.index(prompt) if prompt in labels else prompt))
    for index, prompt in enumerate(prompts, start=1):
        reference = frame.loc[frame.Prompt.eq(prompt), [dimension, "chance_pct"]].drop_duplicates()
        fig.add_trace(go.Scatter(
            x=reference[dimension], y=reference.chance_pct, mode="markers", name="Score au hasard",
            marker=dict(symbol="line-ew-open", size=26, color=GRAY, line=dict(width=4)),
            legendgroup="hasard", showlegend=index == 1,
            hovertemplate="%{x}<br>Hasard %{y:.2f} %<extra></extra>",
        ), row=1, col=index)
    return fig


def horizontal_bars(frame, value, label, colors, title, hover, *, customdata=None):
    fig = go.Figure(go.Bar(
        x=frame[value], y=frame[label], orientation="h", marker_color=colors,
        customdata=customdata, hovertemplate=hover,
    ))
    fig.update_xaxes(title_text=title, zeroline=True, zerolinecolor=GRAY)
    fig.update_yaxes(categoryorder="array", categoryarray=frame[label].tolist(), autorange="reversed")
    return fig


def counts_bars(labels, counts, colors):
    fig = go.Figure(go.Bar(
        x=labels, y=counts, marker_color=colors,
        texttemplate="%{y:,d}", textposition="outside", cliponaxis=False,
        hovertemplate="%{x}<br>%{y:,d} questions<extra></extra>",
    ))
    fig.update_yaxes(title_text="Questions", range=[0, max(1, max(counts) * 1.17)])
    return fig


def connected_categories(frame):
    fig = go.Figure()
    x, y = [], []
    for row in frame.itertuples(index=False):
        x.extend([row.gemma_success_pct, row.ministral_success_pct, None])
        y.extend([row.category, row.category, None])
    fig.add_scatter(x=x, y=y, mode="lines", line=dict(color="#b6c7d7", width=3), showlegend=False, hoverinfo="skip")
    for field, model, symbol, size in (
        ("gemma_success_pct", "Gemma", "circle-open", 13), ("ministral_success_pct", "Ministral", "diamond", 8),
    ):
        color = TEAL if model == "Gemma" else ORANGE
        fig.add_scatter(
            x=frame[field], y=frame.category, mode="markers", name=model,
            marker=dict(color=color, symbol=symbol, size=size, line=dict(width=2)),
            customdata=frame[["gemma_success_pct", "ministral_success_pct"]].to_numpy(),
            hovertemplate="%{y}<br>Gemma %{customdata[0]:.2f} %<br>Ministral %{customdata[1]:.2f} %<extra></extra>",
        )
    fig.update_xaxes(range=[0, 100], ticksuffix=" %", title_text="Réponses justes")
    fig.update_yaxes(categoryorder="array", categoryarray=frame.category.tolist(), autorange="reversed")
    return fig
