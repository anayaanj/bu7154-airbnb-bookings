#!/usr/bin/env bash
# The extension behind the app: run the analysis notebook on every other place in notebooks/cities.py
# (four at a time), then rebuild the app's data files. Run run_all.sh first.
set -euo pipefail
cd "$(dirname "$0")"

python get_data.py --all
mkdir -p outputs/atlas/notebooks outputs/atlas/tables
python -c "import sys; sys.path.insert(0, 'notebooks'); from cities import CITIES, MAIN; print('\n'.join(c for c in CITIES if c not in MAIN))" |
  xargs -P 4 -I {} env CITY="{}" TABLES=../outputs/atlas/tables jupyter nbconvert --to notebook --execute \
    --ExecutePreprocessor.timeout=-1 notebooks/Airbnb_Project_Guided.ipynb --output-dir outputs/atlas/notebooks --output "{}.ipynb" ||
  echo "Some cities failed: they keep the core model only (see the log above)."
python build_atlas.py
