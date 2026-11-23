"""Assemble the dashboard's data files (outputs/dashboard/*.json) from the analysis tables.

Each file is {rows, meta}: meta carries this script and the notebook cell that produced the numbers,
so a reader of the dashboard can see how every figure was computed.
"""
import json
import os

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
TABLES = os.path.join(ROOT, "outputs", "tables")
OUT = os.path.join(ROOT, "outputs", "dashboard")
CITIES = ["London", "Paris"]
REPO = "https://github.com/anayaanj/bu7154-airbnb-bookings"
SELF = open(os.path.abspath(__file__)).read()

LABELS = {
    "superhost": "Superhost", "host_years_z": "Host tenure (+1 SD)", "log_host_listings_z": "Host's listings (+1 SD)",
    "accommodates_z": "Capacity (+1 SD)", "n_amenities_z": "Amenities (+1 SD)", "entire_home": "Entire home",
    "log_price_z": "Price (+1 SD)", "price_missing": "No price (not bookable)",
    "has_profile_pic": "Host profile photo", "identity_verified": "Identity verified", "log_desc_words_z": "Description length",
    "lix_z": "Description readability (LIX)", "promo_per_100_z": "Promotional words", "desc_pos_z": "Description positivity",
    "desc_neg_z": "Description negativity", "review_scores_rating_z": "Overall rating",
    "review_scores_communication_z": "Communication score", "review_scores_cleanliness_z": "Cleanliness score",
    "share_positive_z": "Share of positive reviews", "review_neg_z": "Review negativity",
    "host_response_time": "Host response time", "instant_bookable": "Instant booking",
}
GUEST = ["review_scores_rating_z", "review_scores_communication_z", "review_scores_cleanliness_z",
         "share_positive_z", "review_neg_z", "log_mean_words_z", "share_non_en_z", "log_spread_z"]


def table(name, city=None):
    return pd.read_csv(os.path.join(TABLES, f"{city + '_' if city else ''}{name}.csv"), index_col=0)


def cell(notebook, header):
    nb = json.load(open(os.path.join(ROOT, "notebooks", notebook)))
    return next("".join(c["source"]) for c in nb["cells"]
                if c["cell_type"] == "code" and "".join(c["source"]).startswith(header))


def write(name, rows, cells):
    """cells: [(notebook, header)] whose code produced these numbers."""
    meta = [{"label": "Repository", "value": REPO}]
    for notebook, header in cells:
        meta.append({"label": f"{notebook}, {header.lstrip('# ')}", "value": cell(notebook, header),
                     "type": "code", "lang": "python"})
    meta.append({"label": "build_dashboard_data.py", "value": SELF, "type": "code", "lang": "python"})
    rows = pd.DataFrame(rows).replace({np.nan: None}).to_dict("records")
    with open(os.path.join(OUT, f"{name}.json"), "w") as f:
        json.dump({"rows": rows, "meta": meta}, f, ensure_ascii=False, indent=0)


os.makedirs(OUT, exist_ok=True)
MAIN = "Airbnb_Project_Guided.ipynb"

# 1. One row per city: the data journey and the outcome's dispersion
summary = []
for city in CITIES:
    log = pd.read_csv(os.path.join(ROOT, "data", city, f"{city}_data_log.csv"), header=None, index_col=0)[1]
    M = pd.read_csv(os.path.join(ROOT, "data", city, f"{city}_model_data.csv.gz"), usecols=["number_of_reviews"] + GUEST)
    y = M["number_of_reviews"]
    lang = table("language_share", city)["share"]
    summary.append({
        "city": city, "snapshot": log["Snapshot date (InsideAirbnb)"], "downloaded": log["Download date"], "seed": log["Seed"],
        "raw_listings": int(log["listings.csv.gz raw rows"].replace(",", "")),
        "raw_reviews": int(log["reviews.csv.gz raw rows"].replace(",", "")),
        "sample_listings": int(log["Listings after sampling"].replace(",", "")),
        "sample_reviews": int(log["Reviews after sampling"].replace(",", "")),
        "model_listings": len(M), "reviewed_listings": int((y > 0).sum()),
        "model_b_listings": int(M[y > 0].dropna(subset=GUEST).shape[0]),
        "zero_share": (y == 0).mean(), "mean_reviews": y.mean(), "variance_to_mean": y.var() / y.mean(),
        "english_share": lang.get("en", 0.0),
    })
write("city_summary", summary, [(MAIN, "# Cell 6"), (MAIN, "# Cell 8:"), (MAIN, "# Cell 15")])

# 2. Brief variables that are empty in the files
decisions = {
    "host_response_time": "Cannot be tested", "instant_bookable": "Cannot be tested",
    "host_total_listings_count": "Replaced by host_listings_count", "host_since": "Replaced by hosts_time_as_host_years",
    "price": "Median-filled and flagged (price_missing)",
    "review_scores_rating": "Only for reviewed listings (Model B)", "review_scores_communication": "Only for reviewed listings (Model B)",
    "review_scores_cleanliness": "Only for reviewed listings (Model B)", "first_review": "Only for reviewed listings (Model B)",
    "last_review": "Only for reviewed listings (Model B)",
}
miss = pd.DataFrame({c: table("missing_fields", c)["share_missing"] for c in CITIES})
write("missing_fields", [{"field": f, "london_missing": r["London"], "paris_missing": r["Paris"],
                          "decision": decisions.get(f, "Used as given")} for f, r in miss.iterrows() if r.max() > 0],
      [(MAIN, "# Cell 4")])

# 3. Observed vs predicted distribution of reviews
write("count_fit", [{"city": c, "reviews": b, "observed": r["Observed"], "poisson": r["Poisson"],
                     "negative_binomial": r["Negative Binomial"]}
                    for c in CITIES for b, r in table("count_fit", c).iterrows()], [(MAIN, "# Cell 16")])
write("model_fit", [{"city": c, "model": m, "aic": t.loc["AIC", m], "bic": t.loc["BIC", m],
                     "predicted_zero_share": t.loc["predicted share of zeros", m]}
                    for c in CITIES for t in [table("model_fit", c)] for m in t.columns], [(MAIN, "# Cell 16")])

# 4. Every coefficient the story shows, as IRR or odds ratio with its 95% CI
models = {"model_a": "model_a", "hurdle_any_review": "first_review", "hurdle_how_many": "more_reviews",
          "model_ltm": "last_12_months"}  # model ids: Model A, hurdle part 1 (odds ratios), hurdle part 2, Model A on last-12-month reviews
write("effects", [{"city": c, "model": label, "variable": v, "label": LABELS.get(v, v), "irr": r["IRR"],
                   "low": r["low"], "high": r["high"], "p": r["p"]}
                  for name, label in models.items() for c in CITIES for v, r in table(name, c).iterrows()],
      [(MAIN, "# Cell 16"), (MAIN, "# Cell 20"), (MAIN, "# Cell 22")])

# 5. What a host can change
write("scenarios", [{"city": c, "scenario": s, "expected_reviews": r["Expected reviews"],
                     "p_any_review": r["P(at least one review)"]}
                    for c in CITIES for s, r in table("scenarios", c).iterrows()], [(MAIN, "# Cell 21")])

# 6. Listings with and without a price
write("price_missing", [{"city": c, "group": "No price" if g == 1 else "Has a price", **r.to_dict()}
                        for c in CITIES for g, r in table("price_missing", c).iterrows()], [(MAIN, "# Cell 11")])


# 7. Replication scorecard and city differences
def verdict(text):
    if text.startswith("✅"):
        return "Replicated", float(text.split()[-1])
    if text.startswith("❌"):
        return "Opposite", float(text.split()[-1])
    if text.startswith("⚠"):
        return "Not in data", None
    return "Not significant", float(text.split("(")[1].rstrip(")"))


rows = []
for v, r in table("scorecard").iterrows():
    row = {"variable": v, "label": LABELS.get(v, v), "expected": r["expected"], "source": r["source"]}
    for c in CITIES:
        row[f"{c.lower()}_verdict"], row[f"{c.lower()}_irr"] = verdict(r[c])
    rows.append(row)
write("scorecard", rows, [("Compare_Cities.ipynb", "# Replication scorecard")])

pooled = table("pooled_interactions")
write("city_differences", [{"variable": v, "label": LABELS.get(v, v), "london_irr": r["London IRR"],
                            "paris_irr": r["Paris IRR"], "interaction_p": r["interaction p"],
                            "differs": "Yes" if r["differs at 5%"] else "No"} for v, r in pooled.iterrows()],
      [("Compare_Cities.ipynb", "# Pooled Model A")])
print(sorted(os.listdir(OUT)))
