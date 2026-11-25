# Predicting Airbnb Bookings

BU7154 Foundations of Business Analytics, Trinity Business School: group project (Group 11).

**Interactive app:** https://predicting-airbnb-bookings.vercel.app

A host-support team at Airbnb wants to know which listing and host features predict successful bookings, and whether the predictors found by Biswas et al. (2020) and Sengupta et al. (2021) hold in London and Paris. Airbnb does not publish bookings, so the number of guest reviews is the proxy. It is modelled with Negative Binomial count regression, with a hurdle model and a log-linear model as robustness checks.

## Reproduce the analysis

Requires Python 3.12 and about 4 GB of free RAM (peak measured: 3.7 GB).

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
./run_all.sh
```

`run_all.sh` took 8 minutes on a laptop with the data already downloaded; a fresh clone also downloads about 700 MB and scores review sentiment (about 5 more minutes). In order, it:

1. Runs `get_data.py`, which downloads the exact InsideAirbnb snapshots (about 700 MB) and checks them against `data/checksums.sha256`.
2. Runs `notebooks/Airbnb_Project_Guided.ipynb` once for London and once for Paris.
3. Runs `notebooks/Compare_Cities.ipynb` (the pooled two-city model and the replication scorecard).
4. Runs `notebooks/Story_Figures.ipynb`.
5. Runs `build_dashboard_data.py`, which writes the dashboard's data files to `outputs/dashboard/`.
6. Runs `build_atlas.py`, which writes the app's data files to `app/public/data/`.
7. Runs `build_report.py`, which writes the 6-page summary report to `outputs/report.pdf`.

To work on one city interactively, start Jupyter with `CITY=Paris jupyter lab`; London is the default.

## The app and the other 20 places

The app in `app/` tells the analysis as a scroll story for any of 22 places: London, Paris, Dublin, the rest of Ireland, Mexico City and 17 of the cities in Sengupta et al. (2021). London and Paris are the main analysis; the others are an extension that runs the same notebook on each place.

```bash
./run_atlas.sh                       # downloads about 2 GB more, runs the notebook on the other 20 places, rebuilds the app data
cd app && npm install && npm run dev
```

`notebooks/cities.py` lists every place with its snapshot. Each place's snapshot date, download date, row counts and file checksum are in `outputs/tables/atlas_data_log.csv`.

## Data

| City | Snapshot | Listings, raw | Reviews, raw | Analysis sample |
|---|---|---|---|---|
| London | 2026-09-17 | 91,954 | 2,323,969 | 50,000 listings, 1,267,626 reviews |
| Paris | 2026-09-16 | 77,149 | 2,503,875 | 50,000 listings, 1,626,768 reviews |

- **Source:** [Inside Airbnb](https://insideairbnb.com/get-the-data/), licensed CC BY 4.0. The files were downloaded on 2026-10-17.
- **Field definitions:** the Inside Airbnb Data Dictionary.
- **Sampling:** both cities exceed the brief's 50,000-listing limit, so each sample is drawn at random with seed `BU7154G11`.
- **Translation:** a random sample of 2,000 non-English Paris comments was translated offline with Argos Translate 1.11.0 (free, no account). 1,911 were translated, covering 13 languages; the rest are rare or misdetected languages. The result is committed as `data/Paris/Paris_translated_sample.csv.gz`, so a rerun does not translate again; the first translation downloads about 1.6 GB of language models.

## Layout

```
get_data.py                 download + verify the raw files (--all for every place)
run_all.sh                  run the main analysis in order
run_atlas.sh                run the notebook on the other 20 places
build_atlas.py              the app's data files, from every place's listings and notebook output
build_dashboard_data.py     dashboard data files (JSON) from the result tables
build_report.py             6-page PDF summary report
notebooks/
  Airbnb_Project_Guided.ipynb   Steps 1-8 for one city (CITY environment variable)
  Compare_Cities.ipynb          pooled model with city interactions, replication scorecard
  Story_Figures.ipynb           presentation figures
  models.py                     variable sets and model helpers
  cities.py                     the places analysed and their snapshots
app/                        the interactive app (Svelte, MapLibre, deck.gl, DuckDB-WASM, D3)
data/                       raw and intermediate files (not committed, except data logs and the translation sample)
outputs/
  notebooks/                executed notebooks with all results
  tables/                   result tables (CSV)
  figures/                  presentation figures (PNG)
  dashboard/                data files behind the interactive dashboard
  report.pdf                6-page summary report
  atlas/                    executed notebooks and tables for the other 20 places
```

## References

- Biswas, B., Sengupta, P., & Chatterjee, D. (2020). Examining the determinants of the count of customer reviews in peer-to-peer home-sharing platforms using clustering and count regression techniques. *Decision Support Systems, 135*, 113324.
- Sengupta, P., Biswas, B., Kumar, A., Shankar, R., & Gupta, S. (2021). Examining the predictors of successful Airbnb bookings with Hurdle models: Evidence from Europe, Australia, USA and Asia-Pacific cities. *Journal of Business Research, 137*, 538–554.
- Hutto, C. J., & Gilbert, E. (2014). VADER: A parsimonious rule-based model for sentiment analysis of social media text. *ICWSM*.
- Inside Airbnb. Get the data. https://insideairbnb.com/get-the-data/
