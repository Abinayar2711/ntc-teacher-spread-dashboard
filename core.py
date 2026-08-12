"""Shared vocabulary for both pages.

The one rule lives here: every teacher lands in exactly one bucket -- one of the
twelve `Only ...` buckets, `Two or more categories`, or `None of the 12` -- so
any row of counts adds back to its Teachers total.
"""
from pathlib import Path

import pandas as pd
import streamlit as st

from build_mapping import CATEGORIES

HERE = Path(__file__).parent
DATA = HERE / "data" / "teachers.parquet"
# What ships. The full file stays local (it carries mobile and email); the
# published copy has the same rows without them, and is the only one in git.
PUBLIC = HERE / "data" / "teachers_public.parquet"
CONTACT = ["mobile", "email"]
MAPPING = HERE / "category_mapping.csv"

NONE_LABEL = "(none of these)"
BLANK = "(not recorded)"

TOTAL = "Teachers"
ONLY_ONE = "Only one category"
MULTI = "Two or more categories"
OTHERS = "None of the 12"

# Slots 1-3 of the validated categorical palette, light surface. Three series is
# the all-pairs safe cap, which is exactly what the headline split needs.
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
SPLIT_COLOURS = {ONLY_ONE: BLUE, MULTI: ORANGE, OTHERS: AQUA}
INK, MUTED, GRID, SURFACE = "#0b0b0b", "#898781", "#e1e0d9", "#fcfcfb"


@st.cache_data
def load():
    df = pd.read_parquet(DATA if DATA.exists() else PUBLIC)
    # On the published app those columns are simply absent; every screen that
    # shows them falls back to a blank rather than breaking.
    for c in CONTACT:
        if c not in df.columns:
            df[c] = ""
    df["bucket"] = df["profile"].map(bucket)
    df["split"] = df["profile"].map(split)
    return df


@st.cache_data
def load_mapping():
    return pd.read_csv(MAPPING, dtype=str).fillna("")


def bucket(profile):
    """The single column a teacher belongs to."""
    if profile == NONE_LABEL:
        return OTHERS
    if " + " in profile:
        return MULTI
    return "Only " + profile


def split(profile):
    """The same answer at three-way resolution, for the charts."""
    if profile == NONE_LABEL:
        return OTHERS
    return MULTI if " + " in profile else ONLY_ONE


def pretty(profile):
    """How a combination is written on screen: 'HP & Rural HP'.

    The stored profile keeps ' + ' -- it is the join key everything counts on.
    This is display only.
    """
    return profile.replace(" + ", " & ")


def only_counts(df):
    return {c: int((df["profile"] == c).sum()) for c in CATEGORIES}


def ordered_categories(df):
    """The twelve, biggest `Only` first -- the column order on every table."""
    only = only_counts(df)
    return sorted(CATEGORIES, key=lambda c: -only[c])


def columns_for(df):
    return ["Only " + c for c in ordered_categories(df)] + [MULTI, OTHERS]


def table(scope, by, label, columns):
    """Rows of `by`, columns of disjoint buckets. Each row sums to Teachers."""
    counts = (
        pd.crosstab(scope[by], scope["bucket"])
        .reindex(columns=columns, fill_value=0)
    )
    counts.insert(0, TOTAL, counts.sum(axis=1))
    counts = counts.sort_values(TOTAL, ascending=False)
    counts.index.name = label
    return counts.reset_index()


def combinations(scope):
    m = scope[scope["bucket"] == MULTI]
    out = (
        m["profile"].value_counts()
        .rename_axis("Combination").reset_index(name=TOTAL)
    )
    out["Combination"] = out["Combination"].map(pretty)
    out["% of the column"] = (out[TOTAL] / max(len(m), 1) * 100).round(1)
    return out


def help_text(df):
    only = only_counts(df)
    text = {
        TOTAL: "Everyone in this row. The columns to the right split them up "
               "with no overlap, so they add back to this number.",
        MULTI: "Holds two or more of the 12 categories. Which combination is "
               "not shown here -- the Charts page ranks the combinations.",
        OTHERS: "Holds none of the 12 categories. Certified only in course "
                "types outside them, such as SSSK or the agriculture "
                "programmes.",
    }
    for c in CATEGORIES:
        text["Only " + c] = (
            f"Holds {c} and nothing else out of the 12 categories. Teachers "
            f"who hold {c} *and* something else are in '{MULTI}'."
            + (f" Nationally no teacher holds only {c}, so this column is "
               "empty." if only[c] == 0 else "")
        )
    return text


THE_RULE = (
    "**Every column answers one question: how many of the 12 categories does "
    "this teacher hold?**\n\n"
    f"- **Exactly one** -> the *Only ...* columns. `Only HP` = teaches HP and "
    "nothing else.\n"
    f"- **Two or more** -> all together in *{MULTI}*. Which combination they "
    "are is the profile ranking on the **Charts** page.\n"
    f"- **None of them** -> *{OTHERS}*. Certified only in course types outside "
    "the 12, like SSSK or agriculture.\n\n"
    "So every teacher lands in exactly one column, and every row adds up to "
    "its **Teachers** total."
)
