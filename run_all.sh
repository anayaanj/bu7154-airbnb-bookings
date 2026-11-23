#!/usr/bin/env bash
# Reproduce the whole analysis: verify the data, run the analysis for each city, compare the cities, draw the figures.
set -euo pipefail
cd "$(dirname "$0")"

python get_data.py
mkdir -p outputs/notebooks
run() { jupyter nbconvert --to notebook --execute --ExecutePreprocessor.timeout=-1 "notebooks/$1.ipynb" \
          --output-dir outputs/notebooks --output "$2.ipynb"; }

for city in London Paris; do
  CITY=$city run Airbnb_Project_Guided "Airbnb_$city"
done
run Compare_Cities Compare_Cities
run Story_Figures Story_Figures
python build_dashboard_data.py
python build_report.py
