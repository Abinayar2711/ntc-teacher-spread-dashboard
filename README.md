# NTC Desk — Teachers by region and programme

Streamlit dashboard over `All Teachers Data from NTC Desk 11082026.csv`
(30,269 raw rows → **30,267 teachers**).

```
python3 build_mapping.py   # seeds category_mapping.csv from the export's labels
python3 build_data.py      # -> data/teachers.parquet + data/teachers_public.parquet
streamlit run app.py --server.port 8531
```

## Published

https://ntc-teacher-spread-dashboard.streamlit.app —
github.com/Abinayar2711/ntc-teacher-spread-dashboard on **share.streamlit.io**,
same GitHub account as `taol-teacher-dashboard`.

**Sign-in required.** `auth_gate.py` is the shared gate from the other report
apps: `st.login()` (Google OIDC) plus an `ALLOWED_DOMAINS` check for
`artofliving.org` / `in.artofliving.org`. The domain check is the real boundary,
not decoration — leave it in. Setup and the errors already hit are in
`~/Transfer/Workspace/adhoc/STREAMLIT_AUTH_SETUP.md`; credentials go in the
Cloud app's Secrets, never in git (`.streamlit/secrets.toml.example` shows the
shape). Locally the redirect URI is `http://localhost:8501/oauth2callback`, so
run on the default port when testing the gate.

`build_data.py` writes two files. `data/teachers.parquet` is the full one and
**never leaves this machine**; `data/teachers_public.parquet` is the same 30,267
rows without `mobile` and `email`, and is the only data file in git. `core.load()`
takes the full file when it is there and the published one otherwise, so the app
is identical either way — on the published site the Mobile and Email columns in
the ⚑ panel and the blanks CSV simply read `—`.

To refresh the published numbers: rerun `build_data.py`, then commit and push
`data/teachers_public.parquet`. Streamlit Cloud redeploys on the push.

Two pages, the same numbers on both:

| | |
|---|---|
| **Tables** (`pages/tables.py`) | Every table, and the landing page. The region list expands **in place** — click a region and its districts open underneath it, in the same columns, several at a time. |
| **Diagrams** (`pages/diagrams.py`) | The pictures. Every profile biggest first for one region at a time — `Only HP` and `HP & Rural HP` on one axis — that region's programme reach behind an expander, and at the foot **every region stacked** seven ways on one axis. Bars are headcounts, so compare the *shape* between regions, not the length. |

`core.py` holds what the pages share: the bucketing rule, the column order, the
palette. `figures.py` holds the chart helpers, so the profile ranking is drawn
by one function on both pages. `app.py` is just the navigation.

Only rerun `build_mapping.py` when a fresh export introduces new course types —
it *overwrites* hand edits. Day to day, edit `category_mapping.csv` and rerun
`build_data.py`.

## The one rule

**Every teacher is counted once, in exactly one column, so every row adds up to
its Teachers total.** Each column answers the same question — how many of the
twelve categories does this teacher hold?

- **Exactly one** → the twelve `Only …` columns.
- **Two or more** → all in a single `Two or more categories` column, opened up
  by the profile ranking on the Diagrams page. Combinations are deliberately not
  spread across columns; that is the only way the arithmetic stays honest.
- **None of them** → `None of the 12`.

Click a region row to open its districts, right under that row. The **▾** in the
*Two or more categories* cell opens that row's own combinations — `HP & Rural
HP`, top 10 — for regions and districts alike. Both toggles are plain CSS
(hidden checkboxes, `:checked ~`), so nothing reruns and several can be open at
once. No sidebar, no filters. Every column header carries hover help.

Combinations are written with **&**, not `+`; the stored profile keeps `' + '`
as its join key and `core.pretty()` does the swap for display only.

Two things to know if you touch that page: `st.html` drops the entire `<style>`
block if anything inside it parses as a tag — even `<details>` inside a CSS
comment — and the stylesheet must be emitted outside the `@st.cache_data`
function, or edits to it keep serving the cached copy. The page ships ~1 MB of
markup and takes a few seconds to first paint.

## The second table — how many can teach each programme

Under the first table, same rows, one column per category — headed *HP
teachers*, *Sahaj teachers* and so on, because each is **everyone certified to
teach it**, whether or not they hold others. HP 21,413 · Rural HP 18,999 · YES+
9,962 · Sri Sri Yoga 6,495 · UY/MY/IP 5,216 · YLTP/WLTP 4,752 · Sahaj 2,012 ·
AMP 477 · DSN 173 · Blessing 71 · TTP Happiness 49 · Shakti 31.

**These columns overlap and do not add up** — 69,650 against 30,267 teachers,
because one teacher is counted in every category they hold. It cannot be
reconciled against the first table, and the page says so in a warning above it.
`All teachers` and `No category teachers` are the only non-overlapping columns.

The charts obey the same rule — every slice and every bar segment counts each
teacher once, so they add to the total. The single chart that does *not* (how
many teachers can teach each programme, which overlaps) is behind an expander
behind an expander on the Diagrams page, drawn in grey and labelled as
unaddable.

Colours are the first three slots of a categorical palette validated for
colour-blind separation on the light chart surface (blue `#2a78d6`, orange
`#eb6834`, aqua `#1baf7a`); `.streamlit/config.toml` pins the app to the light
theme so they render against the surface they were checked on.

Four `Only` columns are zero everywhere — DSN, Blessing, Shakti, TTP Happiness.
That is real: every teacher holding those also holds something else, so they all
sit in `Two or more categories`.

## What the file is

One row per teacher. `Course Taught` is a comma-joined list of every course type
the teacher is **certified to teach** — 409 distinct labels, median 17 per
teacher. There are no dates, counts or pax here: this is capability, not
delivery.

Cleaning applied in `build_data.py`:

- Dropped one row that is literally the source field names (`TCH_CODE`,
  `PIN_ZIP`, `APEX_STATE`…) — it was also the source of a third `TCD` value.
- Deduped `SK-UK-1828` (Vandana Markale), which appears twice; kept the later
  `Teacher Since`.
- Blank State / District / City → `(not recorded)` rather than dropped.

## Region

`region` = **Apex**, falling back to the teacher's **State** where Apex is blank,
and `(not recorded)` where neither is filled in.

| | teachers |
|---|---:|
| Apex recorded | 29,995 |
| Apex blank → used State | 175 |
| Neither recorded | 97 |

32 regions. The `(not recorded)` row stays in the table so the total is the
whole file — and carries a **⚑** that opens the teachers behind it: code, name,
Apex, State, district, city, PIN, mobile, email, year since. An empty location
field is spelt out as a red `(not recorded)` rather than dashed — the gap is
what the panel is for. City and PIN are the point —
they are what a missing district can be recovered from without a phone call.
Every `(not recorded)` district row has one too; the full working list is the
download under the table.

## The twelve categories

Defined in `category_mapping.csv` (long format — one label can feed two
categories). All decisions were taken by the user; the reviewed calls on the
originally-flagged labels are kept in `2026-08-11T11-44_export.csv`.

| Category | Notes |
|---|---|
| HP | The five requested labels + **OMBW folded in** (matches `HP+OMBW` in `Trust_Office_Category_Mapping.csv`) + Happiness Connect + Happiness Program for Slums. Plain `Part I Course` does not exist in this export — only `3 Days Part I Course` and `Part 1`. |
| UY/MY/IP | **One combined bucket**: Utkarsha Yoga, Medha Yoga, Intuition Process across all School / Govt. School / Online / SC / Upgrade variants, **plus the teen programmes** `Yes!`, `Yes! 2`, `SMART YES!`, `Rural YES`, `Art Excel`, `Rural ArtExcel`. |
| Rural HP | Rural Happiness Program + its online version. |
| YLTP/WLTP | YLTP, Online YLTP, YLTP TTC, WLTP, OWLTP. |
| YES+ | Adult YES!+ family + SELP / Online SELP. The teen brackets are in UY/MY/IP, not here. |
| AMP | All AMP variants, Online HAMP, `Part 2` (per the Trust Office mapping), Corporate Programs part 2, Prison Program Part 2. |
| DSN | DSN, Special DSN, Rural DSN, YES!+DSN. |
| Blessing | Blessing Course. |
| Sahaj | All Sahaj Samadhi variants incl. 1-on-1 and BCPE Sahaj. |
| Shakti | Shakti Kriya. |
| TTP Happiness | TTP Happiness. |
| Sri Sri Yoga | 53 labels, matched with the classifier the `SSY/` project validated against the `SSY - All Programs` (39) + `SSY Challenges` (4) tags in `coursetype groupings types - website_grouping_tags.csv`. Excludes other desks' yoga: Sahaj, Medha, Utkarsha, Prajñā, SpineCare, TAOL Educators. |

**Combo course types count into both parents.** `Happiness Program + Sahaj
Samadhi Dhyana Yoga` credits HP *and* Sahaj — one course type, but the teacher
can deliver both programmes.

## None of the 12

225 course types belong to no category; a teacher certified **only** in those is
counted here — **3,564 teachers**. Almost entirely SSSK (~2,740 on the
Foundation modules) and the agriculture desk (Natural Farming, Home Gardening,
Eco Enzyme, ~500 each). 12 teachers have no course type recorded at all.

The full list is on the page, with a second column showing how many holders of
each actually land in this bucket — `Padmasadhana Instructor Trg` has 26,384
teachers but 0 here, because every one of them also holds a category.

## Headline numbers

| Category | Only this |
|---|---:|
| HP | 2,794 |
| Sri Sri Yoga | 2,259 |
| UY/MY/IP | 800 |
| Rural HP | 567 |
| Sahaj | 21 |
| YES+ | 3 |
| YLTP/WLTP · AMP | 1 each |
| DSN · Blessing · Shakti · TTP Happiness | 0 |
| **Two or more categories** | **20,257** |
| **None of the 12** | **3,564** |

Biggest combinations: `HP + Rural HP` 5,192 · `HP + Rural HP + YES+` 4,028 ·
`HP + Rural HP + YES+ + Sri Sri Yoga` 950.

## Still open

- `Mini Yoga Program` (2,247) and `APEX YOGA` (149) are not in the SSY tag list,
  so they sit in None of the 12.
- `Sri Sri Natya Yoga` (61) was pulled **into** Sri Sri Yoga by the
  `Sri Sri…Yoga` pattern — it is a dance programme, so this may be wrong.

## PII

The export carries `Mobile` and `Email` for ~99% of teachers. The source CSV and
`data/` are gitignored. Both fields appear in exactly two places, both about
fixing blanks: the **⚑** panel on a *(not recorded)* row (first 30 teachers) and
the *Download the blanks to fix* expander (5,471 teachers — everyone with a
blank Apex, State, District or City). Nowhere else in the app shows them.
