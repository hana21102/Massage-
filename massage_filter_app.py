
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Massage Therapist Finder", layout="wide")

st.title("Massage Therapist Finder")
st.caption("Upload your CSV/Excel, set filters, and download your shortlist.")

uploaded = st.file_uploader("Upload a CSV or Excel file", type=["csv", "xlsx", "xls"])

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

def autodetect_columns(df: pd.DataFrame):
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

if uploaded:
    if uploaded.name.endswith(".csv"):
        df = pd.read_csv(uploaded)
    else:
        df = pd.read_excel(uploaded)

    mapping = autodetect_columns(df)

    col = lambda k: mapping.get(k)

    with st.sidebar:
        st.header("Filters")
        city = st.text_input("City equals", "")
        neighborhood = st.text_input("Neighborhood contains", "")
        gender = st.text_input("Gender equals", "")
        price_min = st.number_input("Price min", min_value=0.0, value=0.0, step=5.0)
        price_max = st.number_input("Price max (0 = no max)", min_value=0.0, value=0.0, step=5.0)
        rating_min = st.number_input("Rating min (0-5)", min_value=0.0, max_value=5.0, value=0.0, step=0.1)
        reviews_min = st.number_input("Reviews min", min_value=0, value=0, step=5)
        years_min = st.number_input("Min years experience", min_value=0.0, value=0.0, step=1.0)
        mobile = st.checkbox("Require mobile / in-home service")
        modalities = st.text_input("Require ALL modalities (comma/semicolon)", "")
        languages = st.text_input("Require ALL languages (comma/semicolon)", "")
        days = st.text_input("Availability includes any of these days (comma)", "")
        keywords = st.text_input("Keywords in Bio/Credentials (comma)", "")
        sort_keys = st.text_input("Sort by (e.g., price,-rating)", "")

    mask = pd.Series([True] * len(df))

    if city and col("city"):
        mask &= df[col("city")].astype(str).str.lower().eq(city.lower())
    if neighborhood and col("neighborhood"):
        mask &= df[col("neighborhood")].astype(str).str.lower().str.contains(neighborhood.lower(), na=False)
    if gender and col("gender"):
        mask &= df[col("gender")].astype(str).str.lower().eq(gender.lower())

    if col("price"):
        price = pd.to_numeric(df[col("price")], errors="coerce")
        if price_min:
            mask &= price.ge(price_min)
        if price_max:
            mask &= price.le(price_max)

    if rating_min and col("rating"):
        rating = pd.to_numeric(df[col("rating")], errors="coerce")
        mask &= rating.ge(rating_min)

    if reviews_min and col("reviews"):
        rev = pd.to_numeric(df[col("reviews")], errors="coerce")
        mask &= rev.ge(reviews_min)

    if years_min and col("yearsexperience"):
        yrs = pd.to_numeric(df[col("yearsexperience")], errors="coerce")
        mask &= yrs.ge(years_min)

    if mobile and col("mobileservice"):
        m = df[col("mobileservice")]
        if m.dtype == object:
            truthy = m.astype(str).str.lower().isin(["true", "yes", "y", "1"])
        else:
            truthy = m.astype(bool)
        mask &= truthy

    def contains_all(h, needles):
        h = str(h).lower()
        return all(n.strip().lower() in h for n in needles if n.strip())

    req_mods = [x.strip() for x in re_split := __import__("re").split(r"[;,]", modalities) if x.strip()]
    req_langs = [x.strip() for x in __import__("re").split(r"[;,]", languages) if x.strip()]
    req_days  = [x.strip().lower() for x in __import__("re").split(r"[;,]", days) if x.strip()]
    req_keys  = [x.strip() for x in __import__("re").split(r"[;,]", keywords) if x.strip()]

    if req_mods and col("modalities"):
        mask &= df[col("modalities")].astype(str).apply(lambda s: contains_all(s, req_mods))
    if req_langs and col("languages"):
        mask &= df[col("languages")].astype(str).apply(lambda s: contains_all(s, req_langs))
    if req_days and col("availability"):
        mask &= df[col("availability")].astype(str).str.lower().apply(lambda s: any(d in s for d in req_days))
    if req_keys:
        bio_col = col("bio")
        cred_col = col("credentials")
        def text_ok(row):
            block = ""
            if bio_col: block += f" {str(row[bio_col])}"
            if cred_col: block += f" {str(row[cred_col])}"
            return contains_all(block, req_keys)
        mask &= df.apply(text_ok, axis=1)

    out = df[mask].copy()

    # Sorting
    if sort_keys:
        keys = [k.strip() for k in sort_keys.split(",") if k.strip()]
        by, ascending = [], []
        for k in keys:
            desc = k.startswith("-")
            key = k[1:] if desc else k
            # direct or canonical
            if key in out.columns:
                by.append(key)
            else:
                lower = key.lower()
                if lower in ALIASES and mapping.get(lower):
                    by.append(mapping[lower])
            ascending.append(not desc)
        if by:
            out = out.sort_values(by=by, ascending=ascending)

    # Reorder useful columns up front
    preferred = [mapping.get(k) for k in [
        "name","city","neighborhood","price","currency","rating","reviews",
        "modalities","gender","languages","mobileservice","availability",
        "yearsexperience","credentials","bio"
    ] if mapping.get(k)]
    trailing = [c for c in out.columns if c not in preferred]
    out = out[preferred + trailing]

    st.success(f"Matched {len(out)} of {len(df)} candidates.")
    st.dataframe(out, use_container_width=True)

    st.download_button(
        "Download results as CSV",
        data=out.to_csv(index=False).encode("utf-8"),
        file_name="filtered_candidates.csv",
        mime="text/csv"
    )
else:
    st.info("Upload your file to begin. You can try the sample CSV from the README.")
