"""Generate category_mapping.csv: every distinct 'Course Taught' label -> category.

Long format (label,category) so one label can feed two categories -- e.g.
'Happiness Program + Sahaj Samadhi Dhyana Yoga' credits both HP and Sahaj,
per the user's call that the combo course type means both programs are taught.

Labels with no row here fall into 'Other' and land teachers in the
'(none of these)' bucket if they hold nothing else.

Edit category_mapping.csv directly to reclassify -- build_data.py reads it,
this script only seeds it. Rerun only to pick up new labels from a fresh export.
"""
import csv
import re
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
SRC = HERE / "All Teachers Data from NTC Desk 11082026.csv"
OUT = HERE / "category_mapping.csv"

# Display order for profile strings; also the column order in the app.
CATEGORIES = [
    "HP",
    "UY/MY/IP",
    "Rural HP",
    "YLTP/WLTP",
    "YES+",
    "AMP",
    "DSN",
    "Blessing",
    "Sahaj",
    "Shakti",
    "TTP Happiness",
    "Sri Sri Yoga",
]

# --- exact-match members -----------------------------------------------------
EXACT = {
    # HP -- user's 5 labels + OMBW folded in (their call), + Happiness Connect
    # which sat in HP+OMBW in Trust_Office_Category_Mapping.csv.
    "HP": [
        "Happiness Program",
        "Happiness Program (3 Days)",
        "Happiness Program for Youth",
        "Happiness Program for Youth-3 Days",
        "3 Days Part I Course",
        "Part 1",
        "Happiness Connect",
        "Happiness Program for Slums",
        "Online Meditation and Breath Workshop",
        "Online Meditation and Breath Workshop - Voucher",
        "Online Meditation and Breath Workshop for Youth",
        # combos -> credited to both parents
        "Happiness Program + Sahaj Samadhi Dhyana Yoga",
        "Happiness Program for Youth + Sahaj Samadhi Dhyana Yoga",
        "Online Meditation and Breath + Sahaj Samadhi Program",
        "Online Meditation and Breath for Youth + Sahaj Samadhi",
    ],
    "Rural HP": [
        "Rural Happiness Program",
        "Online Rural Happiness Program",
    ],
    "YLTP/WLTP": [
        "YLTP",
        "Online YLTP Program",
        "YLTP TTC",
        "WLTP",
        "OWLTP",
    ],
    # Adult YES!+ family plus SELP (user review, 2026-08-11). The teen-bracket
    # programmes -- Yes!, Yes! 2, SMART YES!, Rural YES -- go to UY/MY/IP, not here.
    "YES+": [
        "YES!+",
        "3 Days YES+",
        "Online Yes+",
        "SELP",
        "Online SELP",
    ],
    "AMP": [
        "AMP - 10 Days",
        "AMP - 5 Days",
        "AMP - 7 Days",
        "AMP - Intensive",
        "AMP - Rural",
        "AMP 4 Days",
        "AMP BusyBee",
        "Online 3days AMP",
        "Online 3days AMP - Voucher",
        "Online 4days AMP",
        "Online HAMP",
        "Part 2",  # Part 2 == AMP, per Trust_Office_Category_Mapping.csv
        "Online Part2 BusyBee",
        "Advanced Meditation Program for Government Employees",
        "Corporate Programs part 2",
        "Prison Program Part 2",
    ],
    # Teen / kids programmes that sit with the youth bucket rather than YES+.
    "UY/MY/IP": [
        "Art Excel",
        "Rural ArtExcel",
        "Rural YES",
        "SMART YES!",
        "Yes!",
        "Yes! 2",
    ],
    "TTP Happiness": [
        "TTP Happiness",
    ],
    "DSN": [
        "DSN",
        "Special DSN",
        "Rural DSN",
        "YES!+DSN",
    ],
    "Blessing": [
        "Blessing Course",
    ],
    "Sahaj": [
        "Sahaj Samadhi Dhyana Yoga",
        "Sahaj Samadhi Dhyana Yoga 1on1",
        "Online Sahaj Samadhi Dhyana Yoga",
        "Online Sahaj Samadhi Dhyana Yoga - Voucher",
        "Online Sahaj Samadhi Dhyana Yoga 1on1",
        "Sahaj Samadhi TTP",
        "BCPE Sahaj",
        # combos -> credited to both parents
        "Happiness Program + Sahaj Samadhi Dhyana Yoga",
        "Happiness Program for Youth + Sahaj Samadhi Dhyana Yoga",
        "Online Meditation and Breath + Sahaj Samadhi Program",
        "Online Meditation and Breath for Youth + Sahaj Samadhi",
    ],
    "Shakti": [
        "Shakti Kriya",
    ],
}

# --- pattern members ---------------------------------------------------------
# UY/MY/IP is one combined bucket (user's call). Utkarsha Yoga + Medha Yoga +
# Intuition Process, across all their School / Govt. School / Online / SC /
# Upgrade variants.
UYMYIP_PATTERNS = [
    r"^IP\b",                 # IP Kids/Teens/Junior/Special Needs, IP - Senior
    r"^IP2$",
    r"^Intuition Process",
    r"Utkarsh",               # covers Utkarsha and 'Utkarsh Yoga Upgrade'
    r"Medha ?Yoga",
    r"\bMY1\b",               # Govt. School MY1, Online SC MY1, School Online MY1
    r"\bUY\b",                # Govt. School UY, Online SC UY, School Online UY
    r"UYMY",                  # TTP Rural UYMY
    r"^TTP MEDHAYOGA$",
]

# Sri Sri Yoga desk. Same classifier the SSY/ reporting project settled on --
# source of truth is the `SSY - All Programs` (39) + `SSY Challenges` (4) tags in
# `coursetype groupings types - website_grouping_tags.csv`, matched by pattern
# because the labels carry mojibake and double spaces. Deliberately excludes
# other desks' yoga: Sahaj, Medha, Utkarsha, Prajna, SpineCare, TAOL Educators.
SSY_PATTERNS = [
    r"SRI\s*SRI.*YOGA",       # incl. Sri Sri Lemurrian Yoga, confirmed in-desk
    r"\bSSY\b",
    r"SSSY",
    r"YOGA\s*TEACHER.*TRAINING",
    r"YOGA\s*TTC",
    r"YOGA\s+FOR\s+WOMEN",
    r"^YOGA@WORK",
    r"^SYP\s",
    r"YOGA\s*CHALLENGE",
    r"HATHA\s*YOGA",
    r"^\d+H\b.*YOGA",         # 200H / 300H / 350 HR TTCs
    r"PRE\s*NATAL\s*YOGA",
    r"PRENATAL\s*YOGA",
    r"QCI\s*YOGA",
    r"CHILDREN\s*YOGA\s*TEACHER",
]

# Labels deliberately left OUT of a category but close enough that someone will
# ask. The 12 originally flagged here were reviewed by the user on 2026-08-11
# (2026-08-11T11-44_export.csv) and all assigned above; nothing outstanding.
FLAGGED: dict[str, str] = {}


def distinct_labels(path: Path) -> list[str]:
    df = pd.read_csv(path, dtype=str, usecols=["Teacher Code", "Course Taught"])
    df = df[df["Teacher Code"] != "TCH_CODE"]  # junk header row in the export
    seen = set()
    for cell in df["Course Taught"].fillna(""):
        for label in cell.split(", "):
            label = label.strip()
            if label:
                seen.add(label)
    return sorted(seen)


def categories_for(label: str) -> list[str]:
    cats = [c for c, members in EXACT.items() if label in members]
    if any(re.search(p, label) for p in UYMYIP_PATTERNS):
        cats.append("UY/MY/IP")
    upper = label.upper()
    if any(re.search(p, upper) for p in SSY_PATTERNS):
        cats.append("Sri Sri Yoga")
    return sorted(set(cats), key=CATEGORIES.index)


def main() -> None:
    labels = distinct_labels(SRC)
    rows = []
    for label in labels:
        cats = categories_for(label)
        if cats:
            rows.extend({"course_label": label, "category": c, "note": ""} for c in cats)
        else:
            rows.append(
                {"course_label": label, "category": "", "note": FLAGGED.get(label, "")}
            )

    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["course_label", "category", "note"])
        w.writeheader()
        w.writerows(rows)

    mapped = sum(1 for r in rows if r["category"])
    print(f"{len(labels)} distinct labels -> {OUT.name}")
    print(f"  {mapped} category rows, {len(labels) - len(set(r['course_label'] for r in rows if r['category']))} labels left as Other")
    for cat in CATEGORIES:
        n = sum(1 for r in rows if r["category"] == cat)
        print(f"    {cat:10s} {n:3d} labels")


if __name__ == "__main__":
    main()
