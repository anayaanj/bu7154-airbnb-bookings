"""Model A for every atlas city: download the listings snapshot, build the core features exactly as
Airbnb_Project_Guided.ipynb does (Cells 5, 10, 14), fit Poisson, Negative Binomial and the hurdle logit,
and write the files behind the app to app/public/data/.

London and Paris reuse the files of the main analysis, so their estimates must equal outputs/tables/*_model_a.csv.
"""
import hashlib
import json
import os
import sys

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats
from statsmodels.discrete.truncated_model import TruncatedLFNegativeBinomialP

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "notebooks"))
from cities import BASE, CITIES, DERIVED, download_date, snapshot  # noqa: E402
from models import CORE, EXPECTED, cluster, fit_nb, formula, replication  # noqa: E402

SEED = "BU7154G11"
SEED_INT = int(hashlib.md5(SEED.encode()).hexdigest(), 16) % (2**32)
MAX_LISTINGS = 50000
OUT = os.path.join(ROOT, "app", "public", "data")
CORE_CONT = ["host_years", "log_host_listings", "accommodates", "n_amenities", "log_price"]
MAX_COUNT = 80   # the distribution chart shows 0..80 reviews
MIN_COMMENTS = 300   # sentiment is shown for months with at least this many English comments



def slug(city):
    return city.lower().replace(" ", "-")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def data(city, name):
    return os.path.join(ROOT, "data", city, name)


def features(raw):
    """Cell 5 (sample), Cell 10 (core variables) and Cell 14 (drop missing, standardise) of the main notebook."""
    D = raw.sample(n=MAX_LISTINGS, random_state=SEED_INT) if len(raw) > MAX_LISTINGS else raw.copy()
    F = D[["id", "host_id", "number_of_reviews", "number_of_reviews_ltm", "longitude", "latitude", "room_type"]].copy()
    F["neighbourhood"] = D["neighbourhood_cleansed"] if "neighbourhood_cleansed" in D else ""
    F["rating"] = D["review_scores_rating"]
    F["long_stay"] = (D["minimum_nights"] >= 30).astype(int)   # bookable only for 30 nights or more
    F["superhost"] = (D["host_is_superhost"] == "t").astype(int)
    F["host_years"] = D["hosts_time_as_host_years"]
    F["log_host_listings"] = np.log1p(D["host_listings_count"])
    F["accommodates"] = D["accommodates"]
    F["n_amenities"] = D["amenities"].map(lambda a: len(json.loads(a)))
    F["entire_home"] = (D["room_type"] == "Entire home/apt").astype(int)
    price = pd.to_numeric(D["price"].astype("string").str.replace(r"[$,]", "", regex=True), errors="coerce")
    F["price"] = price
    F["price_missing"] = price.isna().astype(int)
    F["log_price"] = np.log(price.fillna(price.median()))
    F = F[~F[CORE_CONT].isna().any(axis=1)].copy()
    scale = {v: {"mean": F[v].mean(), "sd": F[v].std()} for v in CORE_CONT}
    for v in CORE_CONT:
        F[f"{v}_z"] = (F[v] - scale[v]["mean"]) / scale[v]["sd"]
    return F, scale, price.median()


def coefficients(res, extra=()):
    ci = res.conf_int()
    return {v: {"b": res.params[v], "low": ci.loc[v, 0], "high": ci.loc[v, 1], "p": res.pvalues[v]}
            for v in ["Intercept"] + CORE + list(extra)}


def attempt(fit):
    """A secondary model that fails to converge is left out (null in the app), not fatal."""
    try:
        return fit()
    except Exception as error:
        print(f"    secondary model skipped: {type(error).__name__}: {error}")
        return None


def more_reviews(M):
    """Hurdle part 2 (Cell 20): how many reviews, among listings with at least one."""
    P = M[M["number_of_reviews"] > 0]
    res = TruncatedLFNegativeBinomialP.from_formula(formula(CORE), P, truncation=0).fit(
        method="bfgs", maxiter=3000, disp=0, **cluster(P))
    assert res.mle_retvals["converged"], "Truncated Negative Binomial did not converge"
    return coefficients(res)


def analyse(city):
    path = data(city, "listings.csv.gz")   # from get_data.py --all
    raw = pd.read_csv(path, low_memory=False)
    M, scale, price_median = features(raw)
    y = M["number_of_reviews"]

    pois = smf.poisson(formula(CORE), M).fit(maxiter=200, disp=0, **cluster(M))
    nb = fit_nb(CORE, M)
    M["any_review"] = (y > 0).astype(int)
    logit = smf.logit(formula(CORE, "any_review"), M).fit(disp=0, **cluster(M))

    # The same model on reviews from the last 12 months (Cell 22), on later reviews only (hurdle part 2),
    # and with a control for month-plus minimum stays, which some cities' rental rules make common.
    recent = attempt(lambda: coefficients(fit_nb(CORE, M, y="number_of_reviews_ltm")))
    later = attempt(lambda: more_reviews(M))
    long_stay = attempt(lambda: coefficients(fit_nb(CORE + ["long_stay"], M), extra=["long_stay"]))

    alpha = nb.params["alpha"]
    mu_p, mu_nb, size = pois.predict(M).values, nb.predict(M).values, 1 / alpha
    k = np.arange(MAX_COUNT + 1)[:, None]
    pmf = {"observed": np.bincount(y.clip(upper=MAX_COUNT + 1), minlength=MAX_COUNT + 2)[:MAX_COUNT + 1] / len(M),
           "poisson": stats.poisson.pmf(k, mu_p).mean(axis=1),
           "negative_binomial": stats.nbinom.pmf(k, size, size / (size + mu_nb)).mean(axis=1)}

    path_, country, lon, lat, currency, in_paper = CITIES[city]
    info = {
        "city": city, "slug": slug(city), "country": country, "lon": lon, "lat": lat, "currency": currency,
        "in_sengupta_2021": in_paper, "snapshot": snapshot(city),
        "source": f"{BASE}/{DERIVED[city][1] if city in DERIVED else path_}/data/listings.csv.gz", "sha256": sha256(path),
        "download_date": download_date(city), "listings_raw": len(raw), "listings_analysed": len(M),
        "share_zero_reviews": (y == 0).mean(), "mean_reviews": y.mean(), "median_reviews": y.median(),
        "variance_to_mean": y.var() / y.mean(), "share_superhost": M["superhost"].mean(),
        "share_entire_home": M["entire_home"].mean(), "median_price": price_median,
        "median_amenities": M["n_amenities"].median(), "share_long_stay": M["long_stay"].mean(),
        "scale": scale, "alpha": alpha,
        "negative_binomial": coefficients(nb), "any_review_logit": coefficients(logit),
        "last_12_months": recent, "more_reviews": later, "with_long_stay": long_stay, "deep": deep(city),
        "fit": {"aic_poisson": pois.aic, "aic_negative_binomial": nb.aic,
                "zeros_poisson": np.exp(-mu_p).mean(), "zeros_negative_binomial": ((1 + alpha * mu_nb) ** (-size)).mean()},
        "pmf": {name: values.round(6).tolist() for name, values in pmf.items()},
    }

    points = M[["longitude", "latitude", "number_of_reviews", "number_of_reviews_ltm", "superhost", "host_years",
                "accommodates", "n_amenities", "entire_home", "room_type", "neighbourhood", "price", "rating"]].copy()
    points["expected_reviews"] = mu_nb
    points = points.astype({"longitude": "float32", "latitude": "float32", "price": "float32", "rating": "float32",
                            "expected_reviews": "float32", "number_of_reviews": "int32", "number_of_reviews_ltm": "int32",
                            "superhost": "int8", "entire_home": "int8", "accommodates": "int16", "n_amenities": "int16",
                            "host_years": "float32"})
    points.to_parquet(os.path.join(OUT, "points", f"{slug(city)}.parquet"), index=False, compression="zstd")
    return info


def check_against_main_analysis(info):
    """London and Paris must reproduce the notebook's Model A, last-12-months model and hurdle."""
    for key, table in [("negative_binomial", "model_a"), ("last_12_months", "model_ltm"),
                       ("any_review_logit", "hurdle_any_review"), ("more_reviews", "hurdle_how_many")]:
        published = pd.read_csv(os.path.join(ROOT, "outputs", "tables", f"{info['city']}_{table}.csv"), index_col=0)["IRR"]
        ours = pd.Series({v: np.exp(info[key][v]["b"]) for v in CORE})
        assert np.allclose(ours, published[CORE], rtol=1e-3), f"{info['city']}: {table} differs from outputs/tables"
    card = pd.read_csv(os.path.join(ROOT, "outputs", "tables", "scorecard.csv"), index_col=0)[info["city"]]
    for v, e in info["deep"]["estimates"].items():
        assert f"{e['irr']:.2f}" in card[v], f"{info['city']}: scorecard estimate for {v} differs from outputs/tables"


def deep(city):
    """The scorecard estimates (Models A, A+ and B), for cities the analysis notebook has been run on."""
    path = data(city, f"{city}_model_data.csv.gz")
    if not os.path.exists(path):
        return None
    estimates = replication(pd.read_csv(path), run=attempt)
    return {"estimates": {v: {"irr": estimates.loc[v, "IRR"], "p": estimates.loc[v, "p"]} for v in EXPECTED if v in estimates.index}}


def sentiment(city):
    """Monthly review volume and VADER sentiment of English comments, from the analysis notebook's review files."""
    if not os.path.exists(data(city, f"{city}_review_sentiment.csv.gz")):
        return None
    R = pd.read_csv(data(city, f"{city}_reviews_clean.csv.gz"), keep_default_na=False,
                    usecols=["listing_id", "date", "text", "is_en"])
    S = pd.read_csv(data(city, f"{city}_review_sentiment.csv.gz"))
    E = R[(R["is_en"] == 1) & (R["text"] != "")]   # the comments Cell 10 scored, in the same order
    assert (E["listing_id"].values == S["listing_id"].values).all(), f"{city}: sentiment scores do not line up with reviews"
    E = E.assign(compound=S["compound"].values, month=E["date"].str[:7])
    months = pd.DataFrame({
        "reviews": R.groupby(R["date"].str[:7]).size(),
        "english": E.groupby("month").size(),
        "positive": E.groupby("month")["compound"].apply(lambda s: (s >= 0.05).mean()),
        "negative": E.groupby("month")["compound"].apply(lambda s: (s <= -0.05).mean()),
        "mean": E.groupby("month")["compound"].mean(),
    })
    months = months[months["english"] >= MIN_COMMENTS].iloc[:-1]   # the snapshot month is incomplete
    return {"city": city, "slug": slug(city), "reviews_total": len(R), "english_total": len(E),
            "months": months.rename_axis("month").reset_index().to_dict("records")}


def clean(o):
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items()}
    if isinstance(o, list):
        return [clean(v) for v in o]
    if isinstance(o, float) and np.isnan(o):
        return None
    if isinstance(o, (float, np.floating)):
        return round(float(o), 6)
    if isinstance(o, np.integer):
        return int(o)
    return o


if __name__ == "__main__":
    os.makedirs(os.path.join(OUT, "points"), exist_ok=True)
    cities = []
    for city in sys.argv[1:] or CITIES:
        try:
            info = analyse(city)
        except Exception as error:   # one city failing must not stop the rest; it is reported and left out
            print(f"{city}: SKIPPED ({type(error).__name__}: {error})")
            continue
        if city in ("London", "Paris"):
            check_against_main_analysis(info)
        cities.append(clean(info))
        print(f"{city}: {info['listings_analysed']:,} listings, {info['share_zero_reviews']:.1%} never reviewed, "
              f"superhost IRR {np.exp(info['negative_binomial']['superhost']['b']):.2f}", flush=True)
    if not sys.argv[1:]:
        with open(os.path.join(OUT, "cities.json"), "w") as f:
            json.dump(cities, f, ensure_ascii=False, indent=1)
        with open(os.path.join(OUT, "sentiment.json"), "w") as f:
            json.dump(clean([s for s in map(sentiment, CITIES) if s]), f, ensure_ascii=False)
        log = pd.DataFrame(cities)[["city", "snapshot", "download_date", "source", "sha256", "listings_raw", "listings_analysed"]]
        log.to_csv(os.path.join(ROOT, "outputs", "tables", "atlas_data_log.csv"), index=False)
