"""Retrieve the authors' calibrated maps and stereo products."""
import hashlib
import os
from pathlib import Path
from zipfile import ZipFile

import requests

ROOT = Path(__file__).resolve().parent
DATA = Path(os.environ.get("MCGETCHIN_DATA", ROOT / "data"))
BASE = "https://zenodo.org/api/records/21481275/files/"
ARCHIVES = {
    "NAC_32bit_data.zip": ("f0ed59da33242489d5817819433af2f5", [
        "M146540098LR_32bit.tif", "M1273794308R_32bit.tif",
        "M1519004052LR_32bit.tif", "M1521345601L_32bit.tif",
        "M1523687730LR_32bit.tif"]),
    "DTM_data.zip": ("d8c6172a4940ec054f0730eb91426619", [
        "NAC_DTM_NEW200CRAT3_M1521338586_100cm_crop.tif",
        "NAC_DTM_NEW200CRAT3_M1521352616_100cm_crop.tif",
        "NAC_DTM_NEW200CRAT3_E014N0671_crop.tif"]),
}


def fetch():
    DATA.mkdir(parents=True, exist_ok=True)
    for name, (checksum, members) in ARCHIVES.items():
        path = DATA / name
        if not path.exists():
            with requests.get(BASE + name + "/content", stream=True) as response:
                response.raise_for_status()
                temp = path.with_suffix(".partial")
                with temp.open("wb") as out:
                    for chunk in response.iter_content(1024 * 1024):
                        out.write(chunk)
            if hashlib.md5(temp.read_bytes()).hexdigest() != checksum:
                raise ValueError(f"Zenodo checksum mismatch for {name}")
            temp.replace(path)
        if hashlib.md5(path.read_bytes()).hexdigest() != checksum:
            raise ValueError(f"Zenodo checksum mismatch for {name}")
        with ZipFile(path) as archive:
            for member in members:
                (DATA / member).write_bytes(archive.read(member))
        print(f"Verified {name}, extracted {len(members)} map products")


if __name__ == "__main__":
    fetch()
