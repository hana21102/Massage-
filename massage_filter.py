
#!/usr/bin/env python3
"""
Filter a list of massage therapist candidates stored in CSV or Excel.

Quick start:
  python massage_filter.py --in massage_candidates.csv --city "Vancouver" \
      --price-max 110 --rating-min 4.6 --modalities "Deep Tissue, Sports" \
      --languages "English" --out results.csv --sort "price,-rating"

File formats: .csv, .xlsx, .xls
Column names are flexible (case-insensitive); common aliases are auto-detected.

Recommended columns (any subset is fine):
  Name, City, Neighborhood, Price, Currency, Rating, Reviews, Modalities,
  Gender, Languages, MobileService, Availability, YearsExperience, Credentials, Bio
"""
import argparse
import sys
import re
from typing import Dict, List, Optional
import pandas as pd
from pathlib import Path

ALIASES = {
    "name": ["name", "therapist", "provider"],
    "city": ["city", "location_city", "town"],
    "neighborhood": ["neighborhood", "area", "district", "borough"],
    "price": ["price", "rate", "fee", "session_cost"],
    "currency": ["currency", "price_currency"],
    "rating": ["rating", "score", "stars"],
    "reviews": ["reviews", "review_count"],
    "modalities": ["modalities", "techniques", "specialties", "services"],
    "gender": ["gender", "therapist_gender"],
    "languages": ["languages", "language"],
    "mobileservice": ["mobileservice", "mobile", "in_home", "house_call"],
    "availability": ["availability", "hours", "schedule"],
    "yearsexperience": ["yearsexperience", "experience_years", "yrs_exp", "experience"],
    "credentials": ["credentials", "license", "certifications"],
    "bio": ["bio", "about", "description", "summary"],
}

def autodetect_columns(df: pd.DataFrame) -> Dict[str, Optional[str]]:
    cols = {c.lower(): c for c in df.columns}
    mapping = {}
    for canon, aliases in ALIASES.items():
        found = None
        for a in aliases:
            if a in cols:
                found = cols[a]
                break
        mapping[canon] = found
    return mapping

def split_list(s: Optional[str]) -> List[str]:
    if not s:
        return []
    # split on comma or semicolon
    return [x.strip() for x in re.split(r"[;,]", s) if x.strip()]

def contains_all(haystack: str, needles: List[str]) -> bool:
    h = haystack.lower()
    return all(n.lower() in h for n in needles)

def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="infile", required=True,
                   help="Input CSV/Excel (e.g., candidates.csv)")
    p.add_argument("--out", dest="outfile", default=None,
                   help="Optional: write filtered results here (CSV)")
    p.add_argument("--city", help="Filter by city (case-insensitive exact match)")
    p.add_argument("--neighborhood", help="Filter by neighborhood (case-insensitive contains)")
    p.add_argument("--gender", help="Filter by therapist gender (case-insensitive exact match)")
    p.add_argument("--modalities", help="Require ALL these modalities (comma/semicolon separated)")
    p.add_argument("--languages", help="Require ALL these languages (comma/semicolon separated)")
    p.add_argument("--price-min", type=float, default=None)
    p.add_argument("--price-max", type=float, default=None)
    p.add_argument("--rating-min", type=float, default=None)
    p.add_argument("--reviews-min", type=int, default=None)
    p.add_argument("--years-min", type=float, default=None, help="Minimum years of experience")
    p.add_argument("--mobile", action="store_true", help="Require mobile/in-home service")
    p.add_argument("--text", help="Keyword(s) that must appear in Bio/Credentials (comma-separated)")
    p.add_argument("--available", help="Day(s) to look for in availability (e.g., 'Mon, Tue, Sat')")
    p.add_argument("--sort", help="Sort by comma-separated keys. Prefix with '-' to sort desc. e.g., 'price,-rating'")

    args = p.parse_args(argv)

    path = Path(args.infile)
    if not path.exists():
        sys.exit(f"Input not found: {path}")

    if path.suffix.lower() in [".xlsx", ".xls"]:
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path)

    # Harmonize column names
    mapping = autodetect_columns(df)

    def col(canon: str) -> Optional[str]:
        return mapping.get(canon)

    # Prepare filters
    req_modalities = split_list(args.modalities)
    req_languages = split_list(args.languages)
    req_text = split_list(args.text)
    req_days = [d.strip().lower() for d in split_list(args.available)]

    mask = pd.Series([True] * len(df))

    # City exact (case-insensitive)
    if args.city and col("city"):
        mask &= df[col("city")].astype(str).str.lower().eq(args.city.lower())

    # Neighborhood contains
    if args.neighborhood and col("neighborhood"):
        mask &= df[col("neighborhood")].astype(str).str.lower().str.contains(args.neighborhood.lower(), na=False)

    # Gender exact
    if args.gender and col("gender"):
        mask &= df[col("gender")].astype(str).str.lower().eq(args.gender.lower())

    # Price range
    if col("price"):
        price = pd.to_numeric(df[col("price")], errors="coerce")
        if args.price_min is not None:
            mask &= price.ge(args.price_min)
        if args.price_max is not None:
            mask &= price.le(args.price_max)

    # Rating min
    if args.rating_min is not None and col("rating"):
        rating = pd.to_numeric(df[col("rating")], errors="coerce")
        mask &= rating.ge(args.rating_min)

    # Reviews min
    if args.reviews_min is not None and col("reviews"):
        rev = pd.to_numeric(df[col("reviews")], errors="coerce")
        mask &= rev.ge(args.reviews_min)

    # Years of experience
    if args.years_min is not None and col("yearsexperience"):
        yrs = pd.to_numeric(df[col("yearsexperience")], errors="coerce")
        mask &= yrs.ge(args.years_min)

    # Mobile service
    if args.mobile and col("mobileservice"):
        # truthy values
        m = df[col("mobileservice")]
        if m.dtype == object:
            truthy = m.astype(str).str.lower().isin(["true", "yes", "y", "1"])
        else:
            truthy = m.astype(bool)
        mask &= truthy

    # Modalities ALL required
    if req_modalities and col("modalities"):
        mask &= df[col("modalities")].astype(str).apply(lambda s: contains_all(s, req_modalities))

    # Languages ALL required
    if req_languages and col("languages"):
        mask &= df[col("languages")].astype(str).apply(lambda s: contains_all(s, req_languages))

    # Availability: any day matches
    if req_days and col("availability"):
        mask &= df[col("availability")].astype(str).str.lower().apply(
            lambda s: any(d in s for d in req_days)
        )

    # Text in Bio/Credentials
    if req_text:
        bio_col = col("bio")
        cred_col = col("credentials")
        def text_ok(row):
            block = ""
            if bio_col: block += f" {str(row[bio_col])}"
            if cred_col: block += f" {str(row[cred_col])}"
            return contains_all(block, req_text)
        mask &= df.apply(text_ok, axis=1)

    result = df[mask].copy()

    # Sorting
    if args.sort:
        keys = [k.strip() for k in args.sort.split(",") if k.strip()]
        by = []
        ascending = []
        for k in keys:
            desc = k.startswith("-")
            key = k[1:] if desc else k
            # map to actual column if it's one of the canonical names
            key_lower = key.lower()
            # try direct match first
            if key in result.columns:
                by.append(key)
            else:
                # try canonical → mapped column
                if key_lower in ALIASES and mapping.get(key_lower):
                    by.append(mapping[key_lower])
                else:
                    # fall back: if user typed a real column name (case-insensitive)
                    matches = [c for c in result.columns if c.lower() == key_lower]
                    if matches:
                        by.append(matches[0])
                    else:
                        print(f"Warning: sort key '{key}' not found; ignored.", file=sys.stderr)
                        continue
            ascending.append(not desc)
        if by:
            result = result.sort_values(by=by, ascending=ascending)

    # Reorder columns: surface the most useful first
    preferred = [mapping.get(k) for k in [
        "name","city","neighborhood","price","currency","rating","reviews",
        "modalities","gender","languages","mobileservice","availability",
        "yearsexperience","credentials","bio"
    ] if mapping.get(k)]
    trailing = [c for c in result.columns if c not in preferred]
    result = result[preferred + trailing]

    # Output
    if args.outfile:
        out = Path(args.outfile)
        result.to_csv(out, index=False)
        print(f"Wrote {len(result)} rows to {out}")
    else:
        # print top 30 nicely
        with pd.option_context("display.max_colwidth", 80, "display.width", 200):
            print(result.head(30).to_string(index=False))

if __name__ == "__main__":
    main()
