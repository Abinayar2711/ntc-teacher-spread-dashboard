"""Page 3 -- the profile ranking, one state at a time.

Exactly the chart from the Charts page, drawn over one region instead of the
whole file. Same bars, same colours, same rule: one row per teacher, so the
bars add back to that region's headcount.
"""
import streamlit as st

from build_mapping import CATEGORIES
from core import MULTI, MUTED, NONE_LABEL, ONLY_ONE, OTHERS, TOTAL, load
from figures import CHART_CFG, hbar, profile_figure, profiles

TOP_N = 16
ALL = "All India"

df = load()

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
