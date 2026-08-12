"""Page 1 -- the picture. Same numbers as the tables page, nothing new.

Every teacher is in exactly one slice of every chart here, so slices add to the
total. The one chart where that is not true (how many teachers can teach each
programme, which overlaps) is kept behind an expander and labelled as such.
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from build_mapping import CATEGORIES
from core import (
    AQUA, BLUE, GRID, INK, MULTI, MUTED, NONE_LABEL, ONLY_ONE, ORANGE, OTHERS,
    SPLIT_COLOURS, TOTAL, load, only_counts, ordered_categories,
)
from figures import (
    CHART_CFG, SPLIT_ORDER, frame, hbar, profile_figure, profiles,
)

df = load()
n = len(df)
only = only_counts(df)


# ------------------------------------------------------------------ head -----
st.title("NTC Desk · Teachers")
st.caption(
    f"{n:,} teachers · `All Teachers Data from NTC Desk 11082026.csv`. "
    "Counted for a programme means **certified to teach it** — this file holds "
    "capability, not courses run. Every number here is also on the **Tables** "
    "page."
)

a, b, c, d = st.columns(4)
a.metric("Teachers", f"{n:,}")
b.metric("Regions", f"{df['region'].nunique():,}")
c.metric("Districts", f"{df['district'].nunique():,}")
d.metric("Distinct category profiles", f"{df['profile'].nunique():,}")

# ------------------------------------------------------- the headline split --
st.divider()
st.header("How many of the 12 categories does a teacher hold?")
st.caption(
    "The whole file cut three ways, once. Nobody is in two slices, so the "
    "three add up to every teacher on the NTC Desk."
)

order = [ONLY_ONE, MULTI, OTHERS]
counts = [int((df["split"] == s).sum()) for s in order]

left, right = st.columns([3, 2], gap="large")
with left:
    fig = go.Figure(go.Pie(
        labels=order, values=counts, hole=0.62, sort=False, direction="clockwise",
        marker=dict(colors=[SPLIT_COLOURS[s] for s in order],
                    line=dict(color="#fcfcfb", width=2)),
        texttemplate="%{label}<br><b>%{value:,}</b> · %{percent}",
        textposition="outside", textfont=dict(color=INK, size=13),
        hovertemplate="%{label}<br>%{value:,} teachers · %{percent}<extra></extra>",
    ))
    fig.add_annotation(
        text=f"<b>{n:,}</b><br><span style='font-size:13px;color:{MUTED}'>"
             "teachers</span>",
        showarrow=False, font=dict(size=34, color=INK),
    )
    # Generous top/bottom margin: the slice labels sit outside the ring.
    st.plotly_chart(frame(fig, 460, top=48, left=40, bottom=48),
                    config=CHART_CFG, key="donut")
with right:
    st.markdown(
        f"""
- <span style="color:{BLUE};font-size:22px">●</span> **{ONLY_ONE} — {counts[0]:,}**
  ({counts[0] / n:.0%}). Certified in exactly one of the twelve.
- <span style="color:{ORANGE};font-size:22px">●</span> **{MULTI} — {counts[1]:,}**
  ({counts[1] / n:.0%}). The bulk of the desk: most teachers carry a
  combination, so any single-programme headcount is a slice of this.
- <span style="color:{AQUA};font-size:22px">●</span> **{OTHERS} — {counts[2]:,}**
  ({counts[2] / n:.0%}). Certified only in course types outside the twelve —
  SSSK and the agriculture programmes, mostly.
""",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------- only, by category -
st.divider()
st.header(f"{ONLY_ONE} — which one")
st.caption(
    f"The {counts[0]:,} teachers in the blue slice, opened up. `Only HP` means "
    "HP and nothing else out of the twelve; a teacher who also holds Sahaj is "
    f"not here, they are in *{MULTI}*."
)
cats = ordered_categories(df)
st.plotly_chart(
    hbar(cats, [only[c] for c in cats], BLUE, 460), config=CHART_CFG, key="only")
empty = [c for c in cats if only[c] == 0]
if empty:
    st.caption(
        f"**{', '.join(empty)} sit at zero** — every teacher who holds one of "
        f"those also holds something else, so they are all in *{MULTI}*."
    )

# ------------------------------------------------------------- combinations --
st.divider()
st.header("Every profile, biggest first")
st.caption(
    "The one ranking that puts *Only HP*, *Only UY/MY/IP* and the combinations "
    "on the same axis, so a single-programme teacher can be read against a "
    "combination directly. Colour is the same three-way split as the donut — "
    "still one row per teacher, so no bar overlaps another. One state at a "
    "time is the **By state** page."
)
TOP_N = 16
prof = profiles(df)
shown = prof.head(TOP_N)
st.plotly_chart(profile_figure(shown), config=CHART_CFG, key="profiles")
st.caption(
    f"These {TOP_N} of {len(prof):,} profiles cover "
    f"{shown[TOTAL].sum() / n:.0%} of the desk. The **By state** page runs the "
    f"same ranking for one region; the course types behind {OTHERS} are on the "
    "**Tables** page."
)

# ------------------------------------------------------------------ regions --
st.divider()
st.header("The same split, region by region")

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
st.plotly_chart(fig, config=CHART_CFG, key="regions")
st.caption(
    "Region is the Apex, falling back to the teacher's State where Apex is "
    f"blank. The grey segment is {', '.join(REST)} — "
    + " · ".join(f"{c} {only[c]:,}" for c in REST if only[c])
    + f", and the rest zero. The **Tables** page has every one of the 12 as "
    "its own column, region by region and district by district."
)

# ----------------------------------------------------------------- overlaps --
st.divider()
with st.expander("Reference: how many teachers can teach each programme "
                 "(these overlap — they do not add up)"):
    st.caption(
        "Every chart above counts each teacher once. This one does not: a "
        "teacher certified in HP *and* Sahaj is in both bars, so the bars sum "
        f"to far more than {n:,}. It answers a different question — the reach "
        "of each programme — and is here for reference only."
    )
    reach = sorted(CATEGORIES, key=lambda c: -int(df[c].sum()))
    st.plotly_chart(
        hbar(reach, [int(df[c].sum()) for c in reach], MUTED, 460),
        config=CHART_CFG, key="reach")
    st.caption(
        f"Grey, not blue, because it is the one figure on this dashboard that "
        f"cannot be added up. `Only …` above is the disjoint version of the "
        f"same list. Teachers in none of the twelve: "
        f"{int((df['profile'] == NONE_LABEL).sum()):,}."
    )
