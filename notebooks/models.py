"""Variable sets and model helpers shared by the analysis and comparison notebooks."""
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

# Model A: host and listing features that exist for every listing
CORE = ["superhost", "host_years_z", "log_host_listings_z", "accommodates_z", "n_amenities_z",
        "entire_home", "log_price_z", "price_missing"]
# Model A+: text-mining variables from the description and host profile (Step 4b)
TEXT = ["has_profile_pic", "identity_verified", "has_host_about", "no_description", "legal_only", "desc_not_en",
        "log_desc_words_z", "lix_z", "promo_per_100_z", "desc_pos_z", "desc_neg_z"]
# Model B: guest-side variables, reviewed listings only
GUEST = ["review_scores_rating_z", "review_scores_communication_z", "review_scores_cleanliness_z",
         "share_positive_z", "review_neg_z", "log_mean_words_z", "share_non_en_z", "log_spread_z"]


def usable(data, preds, min_count=20):
    """The predictors that vary enough to estimate: a 0/1 flag needs at least min_count listings on each side."""
    def varies(x):
        return x.value_counts().min() >= min_count if x.nunique() == 2 else x.std() > 0
    return [v for v in preds if varies(data[v])]


def formula(preds, y="number_of_reviews"):
    return f"{y} ~ " + " + ".join(preds)


def cluster(data):
    """Standard errors clustered by host: one host's listings are not independent."""
    return dict(cov_type="cluster", cov_kwds={"groups": data["host_id"]})


def fit_nb(preds, data, y="number_of_reviews"):
    """Negative Binomial (NB2), started from the Poisson estimates: the default start can drift to alpha -> infinity."""
    start = np.append(smf.poisson(formula(preds, y), data).fit(disp=0, maxiter=300).params, 0.5)
    res = smf.negativebinomial(formula(preds, y), data).fit(start_params=start, method="bfgs", maxiter=3000,
                                                            disp=0, **cluster(data))
    assert res.mle_retvals["converged"], "Negative Binomial did not converge"
    return res


def irr(res):
    """exp(coefficient) with 95% CI and p-value: an IRR for count models, an odds ratio for a logit."""
    ci = np.exp(res.conf_int())
    t = pd.DataFrame({"IRR": np.exp(res.params), "low": ci[0], "high": ci[1], "p": res.pvalues})
    return t.drop(index=["Intercept", "alpha"], errors="ignore")


def stars(p):
    return "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else ""


# Replication scorecard: the direction each predictor has in Biswas et al. (2020) and Sengupta et al. (2021)
EXPECTED = {  # variable: (expected sign, source)
    "superhost": ("+", "Both"), "host_years_z": ("+", "Both"), "log_host_listings_z": ("-", "Sengupta"),
    "accommodates_z": ("-", "Sengupta"), "n_amenities_z": ("+", "Both"), "log_price_z": ("-", "Biswas"),
    "has_profile_pic": ("+", "Both"), "identity_verified": ("+", "Biswas"), "log_desc_words_z": ("+", "Both"),
    "lix_z": ("+", "Biswas"), "promo_per_100_z": ("+", "Biswas"), "desc_pos_z": ("-", "Sengupta"), "desc_neg_z": ("+", "Sengupta"),
    "review_scores_rating_z": ("+", "Both"), "review_scores_communication_z": ("+", "Sengupta"),
    "review_scores_cleanliness_z": ("+", "Sengupta"), "share_positive_z": ("+", "Biswas"), "review_neg_z": ("-", "Biswas"),
}


def replication(m, run=lambda fit: fit()):
    """Our estimate of every scorecard predictor: core variables from Model A, text variables from Model A+,
    guest-side variables from Model B. `run` can wrap each fit, e.g. to skip a model that does not converge."""
    reviewed = m[m["number_of_reviews"] > 0].dropna(subset=GUEST)
    parts = [run(lambda: irr(fit_nb(CORE, m))),
             run(lambda: irr(fit_nb(CORE + usable(m, TEXT), m)).drop(index=CORE)),
             run(lambda: irr(fit_nb(CORE + GUEST, reviewed)).drop(index=CORE))]
    return pd.concat([part for part in parts if part is not None])
