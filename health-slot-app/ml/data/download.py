"""Download the Kaggle "Medical Appointment No Shows" dataset to ml/data/noshow.csv.

    python ml/data/download.py

Uses Udacity's public course mirror of the same file (no Kaggle login needed),
then checks the SHA-256 so everyone on the team trains on identical data.
If the mirror is down, download KaggleV2-May-2016.csv from
https://www.kaggle.com/datasets/joniarroba/noshowappointments and save it here
as noshow.csv.
"""
import hashlib
import sys
import urllib.request
from pathlib import Path

URL = (
    "https://d17h27t6h515a5.cloudfront.net/topher/2017/October/"
    "59dd2e9a_noshowappointments-kagglev2-may-2016/noshowappointments-kagglev2-may-2016.csv"
)
SHA256 = "9132d3e7d0246617df9041d3764f20ad6f08e7b0d9f0997fa254fc5e52eda27d"
DEST = Path(__file__).resolve().parent / "noshow.csv"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    if DEST.exists() and sha256(DEST) == SHA256:
        print(f"Already downloaded: {DEST}")
        return
    print(f"Downloading to {DEST} ...")
    urllib.request.urlretrieve(URL, DEST)
    digest = sha256(DEST)
    if digest != SHA256:
        print(f"Checksum mismatch ({digest}). The file may differ from the one the model was trained on.")
        sys.exit(1)
    print("Done. 110,527 appointments, checksum OK.")


if __name__ == "__main__":
    main()
