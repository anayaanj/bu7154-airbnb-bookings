"""Download the exact InsideAirbnb snapshots used in the analysis and verify them against data/checksums.sha256."""
import hashlib
import os
import urllib.request

SNAPSHOTS = {
    "London": "https://data.insideairbnb.com/united-kingdom/england/london/2026-09-17/data",
    "Paris": "https://data.insideairbnb.com/france/ile-de-france/paris/2026-09-16/data",
}
ROOT = os.path.dirname(os.path.abspath(__file__))


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


expected = {}
with open(os.path.join(ROOT, "data", "checksums.sha256")) as f:
    for line in f:
        digest, rel = line.split()
        expected[rel] = digest

for city, base in SNAPSHOTS.items():
    os.makedirs(os.path.join(ROOT, "data", city), exist_ok=True)
    for name in ["listings.csv.gz", "reviews.csv.gz"]:
        rel = f"data/{city}/{name}"
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            print(f"Downloading {rel} ...")
            urllib.request.urlretrieve(f"{base}/{name}", path)
        ok = sha256(path) == expected[rel]
        print(f"{rel}: {'OK' if ok else 'CHECKSUM MISMATCH, delete the file and run again'}")
