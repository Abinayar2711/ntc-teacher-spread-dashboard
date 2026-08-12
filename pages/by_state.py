"""Page 3 -- one state at a time, then all of them side by side.

The profile ranking from the Charts page drawn over one region, the reach of
each programme in that region, and at the foot every region stacked the same
way. Same bars, same colours, same rule: one row per teacher, so the bars add
back to that region's headcount.
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from build_mapping import CATEGORIES
from core import (
    AQUA, GRID, INK, MULTI, MUTED, NONE_LABEL, ONLY_ONE, ORANGE, OTHERS, TOTAL,
    load, only_counts, ordered_categories,
)
from figures import CHART_CFG, frame, hbar, profile_figure, profiles

TOP_N = 16
ALL = "All India"

df = load()
only = only_counts(df)

st.title("Every profile, by state")
st.caption(
    "Pick a region and the ranking is rebuilt for it. Region is the Apex, "
    "falling back to the teacher's State where Apex is blank — the same "
    "geography as the other two pages."
)

sizes = df["region"].value_counts()
choices = [ALL] + list(sizes.index)
picked = st.selectbox(
    "Region", choices, index=0,
    format_func=lambda r: (f"{ALL} — {len(df):,} teachers" if r == ALL
                           else f"{r} — {sizes[r]:,} teachers"),
)

scope = df if picked == ALL else df[df["region"] == picked]
prof = profiles(scope)
shown = prof.head(TOP_N)

a, b, c, d = st.columns(4)
a.metric("Teachers", f"{len(scope):,}")
for col, split in ((b, ONLY_ONE), (c, MULTI), (d, OTHERS)):
    k = int((scope["split"] == split).sum())
    # The share goes in the label, not in `delta` -- a delta draws an arrow,
    # and there is nothing here to be up or down against.
    col.metric(f"{split} · {k / max(len(scope), 1):.0%}", f"{k:,}")

st.plotly_chart(profile_figure(shown), config=CHART_CFG, key="by_state")
st.caption(
    f"Top {len(shown)} of {len(prof):,} profiles in {picked}, covering "
    f"{shown[TOTAL].sum() / max(len(scope), 1):.0%} of its teachers. Bar "
    "lengths are headcounts, not shares, so a small region's chart is short — "
    "read the shape, not the length, when comparing two regions."
)

# The one chart on the page whose bars do not add up -- kept behind an
# expander, in grey, exactly as on the Charts page but for this region only.
with st.expander("Reference: how many teachers can teach each programme "
                 "(these overlap — they do not add up)"):
    st.caption(
        f"The chart above counts each teacher in {picked} once. This one does "
        "not: a teacher certified in HP *and* Sahaj is in both bars, so the "
        f"bars sum to far more than {len(scope):,}. It answers a different "
        "question — the reach of each programme here — and is for reference "
        "only."
    )
    reach = sorted(CATEGORIES, key=lambda c: -int(scope[c].sum()))
    st.plotly_chart(
        hbar(reach, [int(scope[c].sum()) for c in reach], MUTED, 460),
        config=CHART_CFG, key="reach_by_state")
    st.caption(
        "Grey, not blue, because it cannot be added up. Ordered biggest first "
        f"for **{picked}**, so the order itself changes between regions. "
        "Teachers here in none of the twelve: "
        f"{int((scope['profile'] == NONE_LABEL).sum()):,}. The **Tables** page "
        "has the same figures for every region and district at once."
    )

# ----------------------------------------------------------- every region --
st.divider()
st.header("The same split, region by region")
st.caption(
    "Every region at once, whatever is picked above — the ranking of regions "
    "and the shape of each, on one axis."
)

# The four biggest `Only` categories get a segment each; the rest are one
# lump. Eight of the twelve are 26 teachers between them nationally -- as
# segments they would never render a visible pixel, and past eight series the
# palette stops separating for colour-blind readers.
TOP_ONLY = ordered_categories(df)[:4]
REST = [c for c in CATEGORIES if c not in TOP_ONLY]
LUMP = f"Only — the other {len(REST)}"
SEGMENTS = ["Only " + c for c in TOP_ONLY] + [LUMP, MULTI, OTHERS]
# Blue, yellow, green, violet, then the neutral lump, then the two colours
# these buckets already wear on every other chart on the page. Validated for
# colour-blind separation as an adjacent stack on the light surface.
SEG_COLOURS = dict(zip(SEGMENTS, ["#2a78d6", "#eda100", "#008300", "#4a3aa7",
                                  MUTED, ORANGE, AQUA]))
rest_n = sum(only[c] for c in REST)

st.caption(
    f"Each bar is one region's full headcount. *Only one category* is now "
    f"broken into the four that hold almost all of it — {', '.join(TOP_ONLY)} "
    f"— with the remaining {len(REST)} together as one grey segment, because "
    f"they are {rest_n} teachers nationally and would be invisible apart. "
    "Nobody is in two segments, so a bar is still that region's total."
)


def segment(row):
    if row["bucket"] in ("Only " + c for c in TOP_ONLY):
        return row["bucket"]
    return LUMP if row["split"] == ONLY_ONE else row["split"]


seg = df.apply(segment, axis=1)
by_region = (
    pd.crosstab(df["region"], seg).reindex(columns=SEGMENTS, fill_value=0)
)
by_region["_t"] = by_region.sum(axis=1)
by_region = by_region.sort_values("_t", ascending=True)

fig = go.Figure()
for s in SEGMENTS:
    fig.add_trace(go.Bar(
        x=by_region[s], y=by_region.index, orientation="h", name=s,
        marker=dict(color=SEG_COLOURS[s], cornerradius=4,
                    line=dict(color="#fcfcfb", width=2)),
        hovertemplate="%{y}<br>" + s + ": %{x:,}<extra></extra>",
    ))
fig.update_layout(
    barmode="stack", bargap=0.3,
    # Plotly reverses the legend for stacked bars; keep it in bar order.
    legend=dict(orientation="h", yanchor="bottom", y=1.01, x=0, title=None,
                traceorder="normal", font=dict(color=INK)),
)
fig.update_xaxes(showgrid=True, gridcolor=GRID, zeroline=False,
                 tickfont=dict(color=MUTED), title=None, tickformat=",")
fig.update_yaxes(showgrid=False, tickfont=dict(color=INK))
fig = frame(fig, 40 + 24 * len(by_region), top=44, left=0)
fig.update_layout(showlegend=True)
st.plotly_chart(fig, config=CHART_CFG, key="regions_by_state")
st.caption(
    "Region is the Apex, falling back to the teacher's State where Apex is "
    f"blank. The grey segment is {', '.join(REST)} — "
    + " · ".join(f"{c} {only[c]:,}" for c in REST if only[c])
    + f", and the rest zero. The **Tables** page has every one of the 12 as "
    "its own column, region by region and district by district."
)
