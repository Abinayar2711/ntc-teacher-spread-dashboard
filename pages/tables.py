"""Page 2 -- every table. Click a region and its districts open in place.

The region list is rendered as HTML rather than st.dataframe so that a region
expands *under its own row*, with the district numbers sitting in the same
columns, instead of a second table appearing further down the page.
"""
from collections import Counter
from html import escape

import pandas as pd
import streamlit as st

from build_mapping import CATEGORIES
from core import (
    BLANK, MULTI, NONE_LABEL, OTHERS, THE_RULE, TOTAL, columns_for, help_text,
    load, load_mapping, only_counts, pretty, table,
)

df = load()
mapping = load_mapping()
COLUMNS = columns_for(df)
HELP = help_text(df)

CSS = """
<style>
.ntc { --label: 230px; --num: 66px; --multi: 96px;
       /* Teachers, the twelve Only columns, then the wider Two-or-more column
          (it carries the breakdown button) and None of the 12. */
       --cols: var(--label) repeat(13, var(--num)) var(--multi) var(--num);
       font-variant-numeric: tabular-nums; font-size: 13px; color: #0b0b0b;
       border: 1px solid #e1e0d9; border-radius: 8px; overflow: auto;
       max-height: 78vh; background: #fcfcfb; }
/* Cells stretch to the full row height so the pinned first column paints an
   unbroken background over whatever scrolls under it. */
.ntc .row { display: grid; grid-template-columns: var(--cols);
            align-items: stretch; border-top: 1px solid #f0efec;
            /* rows are as wide as the columns, not as the viewport, so row
               backgrounds keep painting past the right edge while scrolling */
            width: max-content; min-width: 100%; }
.ntc .hdr { position: sticky; top: 0; z-index: 2; background: #f0efec;
            border-top: 0; font-size: 11px; line-height: 1.25; color: #52514e; }
.ntc .hdr > div { padding: 8px 8px 6px; display: flex; align-items: flex-end; }
.ntc .c { padding: 7px 8px; display: flex; align-items: center;
          justify-content: flex-end; }
.ntc .c.zero { color: #c3c2b7; }
.ntc .lbl { padding: 7px 8px 7px 10px; font-weight: 600; display: flex;
            align-items: center; position: sticky; left: 0; z-index: 1;
            background: inherit; box-shadow: 1px 0 0 #e1e0d9; }
.ntc .hdr .lbl { background: #f0efec; z-index: 3; }
.ntc .c.tot { font-weight: 700; }

/* Two toggles per row: districts, and the combination breakdown. Each row is
   a group with its own hidden checkboxes rather than a details element, since
   a nested details inside a summary would toggle both at once.
   Keep angle brackets out of this stylesheet entirely: st.html drops the whole
   style tag if it sees anything that parses as a tag, even inside a comment. */
.ntc .grp > .tog { display: none; }
.ntc .pick { display: contents; cursor: pointer; }
.ntc .region { background: #fcfcfb; }
.ntc .region .lbl { background: #fcfcfb; }
.ntc .region:hover, .ntc .region:hover .lbl { background: #f4f4f1; }
.ntc .tog-r:checked ~ .region,
.ntc .tog-r:checked ~ .region .lbl { background: #eef4fd; }
.ntc .region .lbl::before { content: "\\25B8"; color: #2a78d6;
                            display: inline-block; width: 14px;
                            transition: transform .12s; }
.ntc .tog-r:checked ~ .region .lbl::before { transform: rotate(90deg); }
.ntc .kids { display: none; background: #f9f9f7;
             border-left: 3px solid #2a78d6; }
.ntc .tog-r:checked ~ .kids { display: block; }
.ntc .kids .lbl { font-weight: 400; padding-left: 26px; background: #f9f9f7; }
.ntc .kids .row:hover, .ntc .kids .row:hover .lbl { background: #f4f4f1; }

/* The little button in the Two or more categories cell. */
.ntc .c.multi { gap: 6px; }
.ntc .mini { cursor: pointer; user-select: none; font-size: 10px;
             line-height: 15px; width: 17px; height: 17px; text-align: center;
             border-radius: 4px; color: #2a78d6; background: #e8f0fd;
             border: 1px solid #cde2fb; }
.ntc .mini:hover { background: #cde2fb; }
.ntc .tog-c:checked ~ .row .mini { background: #2a78d6; color: #fcfcfb;
                                   border-color: #2a78d6; }
.ntc .combos { display: none; background: #f6f9fe;
               border-left: 3px solid #eb6834; }
.ntc .tog-c:checked ~ .combos { display: block; }
.ntc .combos .inner { position: sticky; left: 0; width: 760px;
                      max-width: 100%; padding: 10px 14px 12px 28px; }
.ntc .combos h4 { margin: 0 0 6px; font-size: 11px; font-weight: 600;
                  letter-spacing: .04em; text-transform: uppercase;
                  color: #52514e; }
/* The whole list is here; long ones scroll inside the panel rather than
   pushing the table down. */
.ntc .combos .list { max-height: 300px; overflow-y: auto;
                     padding-right: 10px; }
.ntc .combos .line { display: grid; grid-template-columns: 1fr 70px;
                     padding: 3px 0; border-top: 1px solid #e9eef7; }
.ntc .combos .line b { font-weight: 400; }
.ntc .combos .line span { text-align: right; font-weight: 600; }
.ntc .combos .foot2 { padding-top: 6px; color: #898781; font-size: 12px; }

/* Who is behind a (not recorded) row -- the same panel machinery, its own
   checkbox, so it opens without disturbing the other two. */
.ntc .mini.flag { color: #b23f12; background: #fdece5; border-color: #f7cdbb;
                  margin-left: 8px; font-weight: 400; }
.ntc .mini.flag:hover { background: #f7cdbb; }
.ntc .tog-p:checked ~ .row .mini.flag,
.ntc .tog-p:checked ~ .region .mini.flag { background: #b23f12;
                                           color: #fcfcfb;
                                           border-color: #b23f12; }
.ntc .people { display: none; background: #fdf6f3;
               border-left: 3px solid #b23f12; }
.ntc .tog-p:checked ~ .people { display: block; }
.ntc .people .inner { position: sticky; left: 0; width: 100%;
                      padding: 10px 14px 12px 28px; }
.ntc .people h4 { margin: 0 0 6px; font-size: 11px; font-weight: 600;
                  letter-spacing: .04em; text-transform: uppercase;
                  color: #52514e; }
/* Nine columns are wider than the page, so the list scrolls both ways inside
   the panel rather than pushing the table around. */
.ntc .people .list { max-height: 300px; overflow: auto; padding-right: 10px; }
/* code, teacher, apex, state, district, city, pin, mobile, email, since */
.ntc .people .line { display: grid;
                     grid-template-columns: 84px 160px 108px 108px 116px 124px
                                            62px 104px 210px 44px;
                     gap: 8px; padding: 3px 0; width: max-content;
                     min-width: 100%; border-top: 1px solid #f2e2da; }
.ntc .people .line.head { position: sticky; top: 0; z-index: 1;
                          background: #fdf6f3; }
.ntc .people .line.head { border-top: 0; color: #898781; font-size: 11px;
                          text-transform: uppercase; letter-spacing: .04em; }
.ntc .people .line b { font-weight: 600; }
/* Long names and addresses are trimmed, not wrapped -- one teacher, one line,
   so the eye can run down the column. The full value is the hover title. */
.ntc .people .line > * { overflow: hidden; text-overflow: ellipsis;
                         white-space: nowrap; }
.ntc .people .line .dim { color: #898781; }
.ntc .people .line .gap { color: #b23f12; background: #fbe6dd;
                          border-radius: 3px; padding: 0 5px; }
.ntc .people .foot2 { padding-top: 6px; color: #898781; font-size: 12px; }
/* The overlapping table: same grid, one column per category. */
.ntc.reach { --num: 78px; --cols: var(--label) repeat(14, var(--num)); }
.ntc .foot { display: grid; grid-template-columns: var(--cols);
             border-top: 2px solid #c3c2b7; font-weight: 700;
             background: #f0efec; position: sticky; bottom: 0; z-index: 2;
             width: max-content; min-width: 100%; }
.ntc .foot .lbl { background: #f0efec; z-index: 3; }
</style>
"""


MULTI_AT = COLUMNS.index(MULTI) + 1   # +1 for the Teachers column in front
VISIBLE_LINES = 12                    # how many fit before the panel scrolls
SAMPLE_ROWS = 30                      # teachers shown inside a blank-row panel


def cells(label, values, combo_id=None, pick=None, people_id=None, extra=""):
    """One grid row. `pick` wraps the plain cells in a label, so clicking
    anywhere but a little button toggles that row's districts."""
    out, own = [], set()   # `own` = cells that carry a button of their own
    for i, v in enumerate([None] + list(values)):
        if i == 0:
            flag = (f'<label class="mini flag" for="{people_id}" title="Who '
                    f'these teachers are">&#9873;</label>' if people_id else "")
            out.append(f'<div class="lbl">{escape(str(label))}{flag}</div>')
            if people_id:
                own.add(i)
        elif i - 1 == MULTI_AT and combo_id and v:
            out.append(
                f'<div class="c multi">{v:,}'
                f'<label class="mini" for="{combo_id}" title="Which '
                f'combinations these are">&#9662;</label></div>'
            )
            own.add(i)
        else:
            klass = "c tot" if i == 1 else ("c zero" if v == 0 else "c")
            out.append(f'<div class="{klass}">{v:,}</div>')
    # A cell holding a button stays outside the row-wide label, so the toggles
    # never fight over the same click; the runs between them are wrapped.
    if pick:
        body, run = "", []
        for i, cell in enumerate(out):
            if i in own:
                if run:
                    body += (f'<label class="pick" for="{pick}">'
                             + "".join(run) + "</label>")
                    run = []
                body += cell
            else:
                run.append(cell)
        if run:
            body += f'<label class="pick" for="{pick}">' + "".join(run) + "</label>"
    else:
        body = "".join(out)
    return f'<div class="row {extra}">' + body + "</div>"


def combo_panel(scope, where):
    """What the Two or more categories number in this row is made of.

    Every combination, biggest first -- no top-N cut, because the question the
    button asks is 'which ones', and a truncated answer only raises it again.
    """
    counts = scope.loc[scope["bucket"] == MULTI, "profile"].value_counts()
    lines = "".join(
        f'<div class="line"><b>{escape(pretty(p))}</b><span>{v:,}</span></div>'
        for p, v in counts.items()
    )
    tail = (f'<div class="foot2">Scroll for the rest — the list thins out to '
            f'combinations held by one or two teachers.</div>'
            if len(counts) > VISIBLE_LINES else "")
    return (
        f'<div class="combos"><div class="inner">'
        f'<h4>{escape(where)} · {int(counts.sum()):,} teachers hold two or '
        f'more, in {len(counts):,} combinations of the 12</h4>'
        f'<div class="list">{lines}</div>{tail}</div></div>'
    )


def people_panel(scope, where, missing):
    """The teachers behind a (not recorded) row, so the blank can be chased.

    A sample only -- the point of the panel is to show what these rows are and
    who to ask; the full list to work through is the download under the table.
    """
    # Apex and State say what the blank sits under; City and PIN are the two
    # fields a missing district can usually be recovered from without a call.
    cols = ["teacher_code", "teacher_name", "apex", "state", "district",
            "city", "pin_code", "mobile", "email", "since"]
    heads = ["Code", "Teacher", "Apex", "State", "District", "City", "PIN",
             "Mobile", "Email", "Since"]
    rows = scope.assign(
        since=pd.to_datetime(scope["teacher_since"], errors="coerce")
        .dt.year.astype("Int64").astype(str).replace({"<NA>": ""}),
    )[cols].sort_values("teacher_code")
    head = ('<div class="line head">'
            + "".join(f"<b>{h}</b>" for h in heads) + "</div>")

    # The location fields say (not recorded) in full rather than a dash: the
    # gap is the thing being shown, so it is spelt out where it happens.
    spelt = {"apex", "state", "district", "city"}

    def cell(c, v):
        text = str(v).strip() if v is not None and str(v) != "None" else ""
        if not text or text == BLANK:
            return (f'<span class="gap" title="Nothing in the export">{BLANK}'
                    '</span>' if c in spelt else '<span class="dim">—</span>')
        tag = "b" if c == "teacher_code" else "span"
        return f'<{tag} title="{escape(text)}">{escape(text)}</{tag}>'

    lines = "".join(
        '<div class="line">'
        + "".join(cell(c, v) for c, v in zip(cols, r))
        + "</div>"
        for r in rows.head(SAMPLE_ROWS).itertuples(index=False)
    )
    tail = (f'<div class="foot2">First {SAMPLE_ROWS} of {len(rows):,}, by code '
            f'— scroll the list sideways for mobile and email. The full list '
            f'is in <b>Download the blanks to fix</b> under the table.</div>'
            if len(rows) > SAMPLE_ROWS else
            '<div class="foot2">Scroll the list sideways for mobile and '
            'email.</div>')
    return (
        f'<div class="people"><div class="inner">'
        f'<h4>{escape(where)} · {len(rows):,} teachers with no {missing} '
        f'recorded</h4><div class="list">{head}{lines}</div>{tail}</div></div>'
    )


@st.cache_data
def region_html():
    regions = table(df, "region", "Region", COLUMNS)
    head = ['<div class="row hdr">',
            '<div class="lbl">Region · District</div>']
    for c in [TOTAL] + COLUMNS:
        head.append(f'<div title="{escape(HELP.get(c, ""))}">{escape(c)}</div>')
    head.append("</div>")

    body = []
    for i, (_, r) in enumerate(regions.iterrows()):
        name = r["Region"]
        vals = [int(r[c]) for c in [TOTAL] + COLUMNS]
        here = df[df["region"] == name]
        kids = table(here, "district", "District", COLUMNS)

        rows = []
        for j, (_, k) in enumerate(kids.iterrows()):
            dname, dcid = k["District"], f"c{i}-{j}"
            kid = here[here["district"] == dname]
            blank = dname == BLANK
            pid = f"p{i}-{j}" if blank else None
            rows.append(
                f'<div class="grp"><input class="tog tog-c" type="checkbox" '
                f'id="{dcid}">'
                + (f'<input class="tog tog-p" type="checkbox" id="{pid}">'
                   if blank else "")
                + cells(dname, [int(k[c]) for c in [TOTAL] + COLUMNS],
                        combo_id=dcid, people_id=pid)
                + combo_panel(kid, f"{name} › {dname}")
                + (people_panel(kid, f"{name} › district", "district")
                   if blank else "")
                + "</div>"
            )
        blank_r = name == BLANK
        body.append(
            f'<div class="grp"><input class="tog tog-r" type="checkbox" '
            f'id="r{i}"><input class="tog tog-c" type="checkbox" id="c{i}">'
            + (f'<input class="tog tog-p" type="checkbox" id="p{i}">'
               if blank_r else "")
            + cells(name, vals, combo_id=f"c{i}", pick=f"r{i}",
                    people_id=f"p{i}" if blank_r else None, extra="region")
            + combo_panel(here, name)
            + (people_panel(here, "No region", "Apex and no state")
               if blank_r else "")
            + f'<div class="kids">{"".join(rows)}</div></div>'
        )

    total = ['<div class="foot">', '<div class="lbl">All India</div>']
    for c in [TOTAL] + COLUMNS:
        total.append(f'<div class="c">{int(regions[c].sum()):,}</div>')
    total.append("</div>")

    # CSS is emitted separately, not from inside this cached function -- a
    # cached string would keep serving the old stylesheet after an edit.
    return ('<div class="ntc">' + "".join(head) + "".join(body)
            + "".join(total) + "</div>")


# -------------------------------------------------------------- reach --------
# The one table on the site whose rows do NOT add up. A teacher certified in
# both HP and Sahaj is counted in both columns, on purpose -- the question here
# is "how many people can deliver this programme", not "who is where".
REACH_COLUMNS = sorted(CATEGORIES, key=lambda c: -int(df[c].sum()))


def reach(scope, by, label):
    g = scope.groupby(by)
    out = pd.DataFrame({TOTAL: g.size()})
    for c in REACH_COLUMNS:
        out[c] = g[c].sum().astype(int)
    out[OTHERS] = g["profile"].apply(lambda s: int((s == NONE_LABEL).sum()))
    out = out.sort_values(TOTAL, ascending=False)
    out.index.name = label
    return out.reset_index()


# Headings say what the number is: "HP teachers", not "HP". Every column on
# this table is a headcount of people who can teach that thing.
REACH_HEAD = {TOTAL: "All teachers", OTHERS: "No category teachers"}
for _c in CATEGORIES:
    REACH_HEAD[_c] = f"{_c} teachers"

REACH_HELP = {
    TOTAL: "Everyone in this row. The category columns overlap, so they do NOT "
           "add up to this — one teacher can be in several of them.",
    OTHERS: "Holds none of the 12. This column and All teachers are the only "
            "two here that do not overlap with anything.",
}
for _c in CATEGORIES:
    REACH_HELP[_c] = (
        f"Everyone certified to teach {_c}, whether or not they also hold "
        f"others. Nationally {int(df[_c].sum()):,} teachers."
    )


def reach_cells(name, row, total, pick=None, extra=""):
    out = [f'<div class="lbl">{escape(str(name))}</div>',
           f'<div class="c tot">{total:,}</div>']
    for c in REACH_COLUMNS + [OTHERS]:
        v = int(row[c])
        out.append(f'<div class="{"c zero" if v == 0 else "c"}">{v:,}</div>')
    body = "".join(out)
    if pick:
        body = f'<label class="pick" for="{pick}">{body}</label>'
    return f'<div class="row {extra}">{body}</div>'


@st.cache_data
def reach_html():
    regions = reach(df, "region", "Region")
    head = ['<div class="row hdr">', '<div class="lbl">Region · District</div>']
    for c in [TOTAL] + REACH_COLUMNS + [OTHERS]:
        head.append(f'<div title="{escape(REACH_HELP[c])}">'
                    f'{escape(REACH_HEAD[c])}</div>')
    head.append("</div>")

    body = []
    for i, (_, r) in enumerate(regions.iterrows()):
        name, tot = r["Region"], int(r[TOTAL])
        kids = reach(df[df["region"] == name], "district", "District")
        rows = "".join(
            reach_cells(k["District"], k, int(k[TOTAL]))
            for _, k in kids.iterrows()
        )
        body.append(
            f'<div class="grp"><input class="tog tog-r" type="checkbox" '
            f'id="x{i}">'
            + reach_cells(name, r, tot, pick=f"x{i}", extra="region")
            + f'<div class="kids">{rows}</div></div>'
        )

    total = ['<div class="foot">', '<div class="lbl">All India</div>',
             f'<div class="c">{len(df):,}</div>']
    for c in REACH_COLUMNS + [OTHERS]:
        total.append(f'<div class="c">{int(regions[c].sum()):,}</div>')
    total.append("</div>")
    return ('<div class="ntc reach">' + "".join(head) + "".join(body)
            + "".join(total) + "</div>")


# ------------------------------------------------------------------ head -----
st.title("NTC Desk · Tables")
st.caption(
    f"{len(df):,} teachers · `All Teachers Data from NTC Desk 11082026.csv`. "
    "Counted for a programme means **certified to teach it**. The **Diagrams** "
    "page is the same numbers as pictures."
)
st.info(THE_RULE + "\n\nHover any column header for its definition.", icon="ℹ️")

# ---------------------------------------------------------------- regions ----
st.header("Region, and the districts inside it")
st.caption(
    "Click a region row — its districts open right underneath, in the same "
    "columns. The small **▾** in the *Two or more categories* cell opens that "
    "row's combinations — `HP & Rural HP`, **all of them**, biggest first, "
    "scrolling inside the panel — without moving anything else; every district "
    "row has one too. Several can be open at "
    "once. A **⚑** appears on every *(not recorded)* row — it opens the "
    "teachers behind that blank: code, name, Apex, State, district, city, PIN, "
    "mobile, email and the year they became a teacher. The missing field shows "
    "as a red *(not recorded)*, so it is clear what has to be filled in. The "
    "table scrolls sideways for the narrower columns; **All India** at the "
    "foot is the whole file."
)
st.html(CSS + region_html())

flat = table(df, "region", "Region", COLUMNS)
st.download_button(
    "Download regions (CSV)", flat.to_csv(index=False).encode("utf-8"),
    "ntc_regions.csv", "text/csv",
)
st.download_button(
    "Download every district (CSV)",
    table(df, "district", "District", COLUMNS).to_csv(index=False).encode("utf-8"),
    "ntc_districts.csv", "text/csv",
)


# ------------------------------------------------------------ the blanks -----
def to_fix():
    """Every teacher with a blank in the fields the table groups by.

    One row per teacher, with what is missing spelt out, so the list can go
    straight back to whoever maintains the record.
    """
    fields = ["apex", "state", "district", "city"]
    blank = df[fields].apply(lambda s: s.fillna("").eq(BLANK) | s.fillna("").eq(""))
    out = df.loc[blank.any(axis=1), [
        "teacher_code", "teacher_name", "region", "apex", "state", "district",
        "city", "pin_code", "mobile", "email", "teacher_since", "profile"]].copy()
    out.insert(2, "Missing", [
        ", ".join(f for f in fields if b[f]) for _, b in
        blank.loc[blank.any(axis=1)].iterrows()])
    return out.sort_values(["region", "teacher_code"])


gaps = to_fix()
with st.expander(f"Download the blanks to fix — {len(gaps):,} teachers", icon="🚩"):
    st.caption(
        "The **⚑** on a *(not recorded)* row shows the first 30 teachers behind "
        "it. This is the whole list, with what is missing spelt out per "
        "teacher — Apex, State, District or City. Mobile and email are "
        "included so the record can be chased; the flag panels and this file "
        "are the only places in the app that show them, so treat it "
        "accordingly."
    )
    st.dataframe(gaps, hide_index=True, width="stretch", height=360)
    st.download_button(
        "Download the blanks (CSV)", gaps.to_csv(index=False).encode("utf-8"),
        "ntc_teachers_blank_location.csv", "text/csv",
    )
    st.caption(
        " · ".join(f"**{f.title()}** blank: {n:,}" for f, n in [
            ("apex", int(gaps["Missing"].str.contains("apex").sum())),
            ("state", int(gaps["Missing"].str.contains("state").sum())),
            ("district", int(gaps["Missing"].str.contains("district").sum())),
            ("city", int(gaps["Missing"].str.contains("city").sum())),
        ])
        + ". A teacher can be counted in more than one of these."
    )

only = only_counts(df)
empty = [c for c in CATEGORIES if only[c] == 0]
if empty:
    st.caption(
        f"All 12 categories have an *Only* column, biggest first. "
        f"{', '.join(empty)} show as zero throughout: every teacher holding "
        f"those also holds something else, so they sit in *{MULTI}*."
    )
if (df["region"] == BLANK).any():
    n = int((df["region"] == BLANK).sum())
    st.caption(
        f"Region is the Apex, or the teacher's State where Apex is blank. The "
        f"*{BLANK}* row is the {n} teachers who have neither — kept in the "
        "table so the total is the full file."
    )

# ----------------------------------------------------------------- reach -----
st.divider()
st.header("How many can teach each programme")
st.warning(
    "**These numbers overlap on purpose — they do not add up.** A teacher "
    "certified in HP *and* Sahaj is counted under **both**, so the category "
    "columns come to more than the Teachers total. Nothing here can be "
    "reconciled against the table above; that one asks *what does this teacher "
    "hold*, this one asks *how many people can deliver this programme*. Read "
    "each column on its own.",
    icon="⚠️",
)
st.caption(
    "Same rows as above — click a region to open its districts. One column per "
    "category, biggest first: *HP teachers* is everyone who can teach HP. "
    "**All teachers** and **No category teachers** are the only two columns "
    "here that overlap with nothing."
)
st.html(CSS + reach_html())

st.download_button(
    "Download the reach table, regions (CSV)",
    reach(df, "region", "Region").rename(columns=REACH_HEAD)
    .to_csv(index=False).encode("utf-8"),
    "ntc_reach_regions.csv", "text/csv",
)
st.download_button(
    "Download the reach table, every district (CSV)",
    reach(df, "district", "District").rename(columns=REACH_HEAD)
    .to_csv(index=False).encode("utf-8"),
    "ntc_reach_districts.csv", "text/csv",
)

# --------------------------------------------------------------- appendix ----
st.divider()
with st.expander("What each category means"):
    st.caption(
        "Built from the `Course Taught` field. A course type may feed two "
        "categories — `Happiness Program + Sahaj Samadhi Dhyana Yoga` is both "
        "HP and Sahaj, because the teacher can deliver both."
    )
    st.dataframe(
        pd.DataFrame([
            {"Category": c,
             "Teachers who hold it": int(df[c].sum()),
             "Course types": int((mapping["category"] == c).sum()),
             "They are": ", ".join(
                 mapping.loc[mapping["category"] == c, "course_label"])}
            for c in CATEGORIES
        ]),
        hide_index=True, width="stretch", height=60 + 35 * len(CATEGORIES),
    )
    st.caption(
        "*Teachers who hold it* overlaps across rows — it is the only figure "
        "on this page that does, and it is here for reference, not for adding "
        "up."
    )

with st.expander(f"What counts as {OTHERS}"):
    others = sorted(mapping.loc[mapping["category"] == "", "course_label"])
    st.caption(
        f"{len(others)} course types belong to none of the twelve categories. "
        "A teacher certified **only** in these is counted under "
        f"*{OTHERS}* — {int((df['profile'] == NONE_LABEL).sum()):,} teachers "
        "nationally. Hold one of these *and* a category course type and you "
        "are counted under that category instead. Spelt as the export has them."
    )
    all_held = Counter(x for row in df["courses"] for x in row)
    b2 = Counter(x for row in df.loc[df["profile"] == NONE_LABEL, "courses"]
                 for x in row)
    st.dataframe(
        pd.DataFrame(
            [{"Course type": l, "Teachers certified in it": all_held.get(l, 0),
              "…of whom counted as None of the 12": b2.get(l, 0)}
             for l in others]
        ).sort_values("Teachers certified in it", ascending=False),
        hide_index=True, width="stretch", height=420,
    )
