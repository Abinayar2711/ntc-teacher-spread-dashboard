"""The chart helpers, shared so a figure looks the same wherever it is drawn.

Colours come from `core`; nothing here decides what a number means.
"""
import plotly.graph_objects as go

from core import (
    INK, MULTI, NONE_LABEL, ONLY_ONE, OTHERS, SPLIT_COLOURS, TOTAL, pretty,
)

CHART_CFG = {"displayModeBar": False}
SPLIT_ORDER = [ONLY_ONE, MULTI, OTHERS]


def frame(fig, height, top=10, left=0, bottom=8):
    fig.update_layout(
        height=height, margin=dict(l=left, r=16, t=top, b=bottom),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family='system-ui, -apple-system, "Segoe UI", sans-serif',
                  size=13, color=INK),
        hoverlabel=dict(font_size=13),
        showlegend=False,
    )
    return fig


def hbar(labels, values, colour, height, gap=0.35):
    """One series, biggest at the top, every bar directly labelled."""
    fig = go.Figure(go.Bar(
        x=values, y=labels, orientation="h",
        marker=dict(color=colour, cornerradius=4),
        text=[f"{v:,}" for v in values], textposition="outside",
        textfont=dict(color=INK),
        hovertemplate="%{y}<br>%{x:,} teachers<extra></extra>",
    ))
    fig.update_layout(bargap=gap)
    fig.update_xaxes(visible=False, range=[0, max(values) * 1.18 or 1])
    fig.update_yaxes(
        autorange="reversed", ticklabelposition="outside",
        tickfont=dict(color=INK), showgrid=False, zeroline=False,
        linecolor="rgba(0,0,0,0)",
    )
    return frame(fig, height)


def profiles(scope):
    """Every profile in `scope`, biggest first, at the parquet's own grain.

    'HP' becomes 'Only HP', combinations stay verbatim, and the leftover
    bucket is a row of its own -- so the counts are the whole of `scope`.
    """
    out = (
        scope["profile"].value_counts()
        .rename_axis("profile").reset_index(name=TOTAL)
    )
    out["split"] = out["profile"].map(
        lambda p: OTHERS if p == NONE_LABEL
        else (MULTI if " + " in p else ONLY_ONE)
    )
    out["label"] = [
        OTHERS if p == NONE_LABEL
        else (pretty(p) if " + " in p else "Only " + p)
        for p in out["profile"]
    ]
    return out


def profile_figure(shown, key_suffix=""):
    """The profile ranking: one bar per profile, coloured by the three-way
    split. Bars are disjoint, so they add back to the scope's headcount."""
    fig = go.Figure()
    for s in SPLIT_ORDER:
        part = shown[shown["split"] == s]
        if part.empty:
            continue
        fig.add_trace(go.Bar(
            x=part[TOTAL], y=part["label"], orientation="h", name=s,
            marker=dict(color=SPLIT_COLOURS[s], cornerradius=4),
            text=[f"{v:,}" for v in part[TOTAL]], textposition="outside",
            textfont=dict(color=INK),
            hovertemplate="%{y}<br>%{x:,} teachers<extra>" + s + "</extra>",
        ))
    fig.update_layout(
        bargap=0.35,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title=None,
                    traceorder="normal", font=dict(color=INK)),
    )
    fig.update_xaxes(visible=False, range=[0, shown[TOTAL].max() * 1.18])
    fig.update_yaxes(
        categoryorder="array", categoryarray=list(shown["label"])[::-1],
        showgrid=False, zeroline=False, linecolor="rgba(0,0,0,0)",
        tickfont=dict(color=INK),
    )
    fig = frame(fig, 40 + 34 * len(shown), top=44)
    fig.update_layout(showlegend=True)
    return fig
