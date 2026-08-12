"""Turn the NTC Desk teacher export into a teacher-grain parquet for the app.

One row per teacher, with a `profile` column = the exact set of categories that
teacher is certified in, joined with ' + '. Profiles are mutually exclusive, so
counts by profile always sum back to the teacher total -- that's the whole point.
"""
from pathlib import Path

import pandas as pd

from build_mapping import CATEGORIES

HERE = Path(__file__).parent
SRC = HERE / "All Teachers Data from NTC Desk 11082026.csv"
MAPPING = HERE / "category_mapping.csv"
OUT_DIR = HERE / "data"
NONE_LABEL = "(none of these)"
BLANK = "(not recorded)"

KEEP = [
    "Teacher Code", "Teacher Name", "AOL ID", "Apex", "State", "District",
    "City", "Pin Code", "Teacher Since", "TCD", "Mobile", "Email",
    "Course Taught",
]


def load_mapping() -> dict[str, frozenset[str]]:
    m = pd.read_csv(MAPPING, dtype=str).fillna("")
    m = m[m["category"] != ""]
    unknown = set(m["category"]) - set(CATEGORIES)
    if unknown:
        raise ValueError(f"category_mapping.csv has unknown categories: {sorted(unknown)}")
    return {
        label: frozenset(g["category"])
        for label, g in m.groupby("course_label")
    }


def clean(df: pd.DataFrame) -> pd.DataFrame:
    # The export carries one row that is literally the source field names.
    df = df[df["Teacher Code"] != "TCH_CODE"]
    # SK-UK-1828 appears twice (a Part Time row and a later Full Time row).
    # Keep the most recent Teacher Since.
    since = pd.to_datetime(df["Teacher Since"], format="%d-%b-%Y", errors="coerce")
    df = df.assign(_since=since).sort_values("_since").drop_duplicates(
        "Teacher Code", keep="last"
    )
    return df.drop(columns="_since")


def main() -> None:
    mapping = load_mapping()
    df = clean(pd.read_csv(SRC, dtype=str, usecols=KEEP))

    courses = df["Course Taught"].fillna("").str.split(", ").apply(
        lambda parts: [p.strip() for p in parts if p.strip()]
    )
    cats = courses.apply(
        lambda cs: {c for label in cs for c in mapping.get(label, ())}
    )

    out = df.drop(columns="Course Taught").rename(
        columns={
            "Teacher Code": "teacher_code", "Teacher Name": "teacher_name",
            "AOL ID": "aol_id", "Apex": "apex", "State": "state",
            "District": "district", "City": "city", "Pin Code": "pin_code",
            "Teacher Since": "teacher_since", "TCD": "tcd",
            "Mobile": "mobile", "Email": "email",
        }
    )
    for col in ("apex", "state", "district", "city"):
        out[col] = out[col].fillna(BLANK).replace("", BLANK).str.strip()
    # 'jammu kashmir ladakh' is the only lowercase apex in the export.
    out["apex"] = out["apex"].str.title().replace({BLANK.title(): BLANK})

    # Region = Apex, falling back to the teacher's own State when Apex is blank
    # (175 teachers), then to nothing at all (97 teachers). Those 97 are shown
    # as their own band in the app rather than mixed into the region list.
    out["region"] = out["apex"].where(out["apex"] != BLANK, out["state"])
    out["region_source"] = "Apex"
    out.loc[out["apex"] == BLANK, "region_source"] = "State (Apex blank)"
    out.loc[out["region"] == BLANK, "region_source"] = "Neither recorded"

    # Verbatim course list is kept so the app can say who the teachers outside
    # the categories actually are, without inventing a taxonomy for them.
    out["courses"] = courses.values
    out["n_courses"] = courses.values
    out["n_courses"] = out["n_courses"].apply(len)
    out["teacher_since"] = pd.to_datetime(
        out["teacher_since"], format="%d-%b-%Y", errors="coerce"
    )
    out["profile"] = cats.apply(
        lambda s: " + ".join(c for c in CATEGORIES if c in s) or NONE_LABEL
    ).values
    out["n_categories"] = cats.apply(len).values
    for cat in CATEGORIES:
        out[cat] = cats.apply(lambda s, c=cat: c in s).values

    OUT_DIR.mkdir(exist_ok=True)
    out.to_parquet(OUT_DIR / "teachers.parquet", index=False)
    # The published copy: same rows, no contact details. This is the only data
    # file committed to the repo, so nothing on the public app can leak a phone
    # number or an email. Locally the full file above is used when it exists.
    out.drop(columns=["mobile", "email"]).to_parquet(
        OUT_DIR / "teachers_public.parquet", index=False)

    print(f"{len(out):,} teachers -> data/teachers.parquet")
    print(f"  regions: {out['region'].nunique()}  " +
          "  ".join(f"{k}={v:,}" for k, v in out["region_source"].value_counts().items()))
    print(f"  {out['profile'].nunique()} distinct profiles")
    print(f"  {(out['profile'] == NONE_LABEL).sum():,} in {NONE_LABEL}")
    for cat in CATEGORIES:
        print(f"    {cat:10s} any={out[cat].sum():6,d}  only={(out['profile'] == cat).sum():5,d}")


if __name__ == "__main__":
    main()
