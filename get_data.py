"""Download the exact InsideAirbnb snapshots used in the analysis and verify them against data/checksums.sha256.

python get_data.py          London and Paris, the two cities of the main analysis
python get_data.py --all    every place in notebooks/cities.py (about 2 GB more)
"""
import hashlib
import os
import sys
import urllib.parse
import urllib.request

import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "notebooks"))
from cities import BASE, CITIES, DERIVED, MAIN  # noqa: E402

FILES = ["listings.csv.gz", "reviews.csv.gz"]
CHECKSUMS = os.path.join(ROOT, "data", "checksums.sha256")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def fetch(source, folder, expected):
    """Download both files of one snapshot; verify a known checksum, record a new one."""
    os.makedirs(os.path.join(ROOT, "data", folder), exist_ok=True)
    for name in FILES:
        rel = f"data/{folder}/{name}"
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            print(f"Downloading {rel} ...", flush=True)
            request = urllib.request.Request(f"{BASE}/{urllib.parse.quote(source)}/data/{name}", headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(request) as response, open(path + ".part", "wb") as f:
                for block in iter(lambda: response.read(1 << 20), b""):
                    f.write(block)
            os.rename(path + ".part", path)
        digest = sha256(path)
        if rel not in expected:
            expected[rel] = digest
            with open(CHECKSUMS, "a") as f:
                f.write(f"{digest}  {rel}\n")
        print(f"{rel}: {'OK' if digest == expected[rel] else 'CHECKSUM MISMATCH, delete the file and run again'}", flush=True)


def derive(city, expected):
    """A place cut out of a larger file: the parent's listings and reviews, minus another place's listings."""
    parent, source, minus = DERIVED[city]
    fetch(source, parent, expected)
    folder = os.path.join(ROOT, "data", city)
    if os.path.exists(os.path.join(folder, "reviews.csv.gz")):
        return
    os.makedirs(folder, exist_ok=True)
    drop = pd.read_csv(os.path.join(ROOT, "data", minus, "listings.csv.gz"), usecols=["id"])["id"]
    listings = pd.read_csv(os.path.join(ROOT, "data", parent, "listings.csv.gz"), low_memory=False)
    listings = listings[~listings["id"].isin(drop)]
    reviews = pd.read_csv(os.path.join(ROOT, "data", parent, "reviews.csv.gz"))
    reviews = reviews[reviews["listing_id"].isin(listings["id"])]
    listings.to_csv(os.path.join(folder, "listings.csv.gz"), index=False)
    reviews.to_csv(os.path.join(folder, "reviews.csv.gz"), index=False)
    print(f"data/{city}: {len(listings):,} listings and {len(reviews):,} reviews of {parent} outside {minus}", flush=True)


if __name__ == "__main__":
    expected = {}
    with open(CHECKSUMS) as f:
        for line in f:
            digest, rel = line.strip().split(maxsplit=1)
            expected[rel] = digest
    for city in (CITIES if "--all" in sys.argv else MAIN):
        if city in DERIVED:
            derive(city, expected)
        else:
            fetch(CITIES[city][0], city, expected)
