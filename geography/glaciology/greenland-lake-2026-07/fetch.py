"""Read the georeferenced science windows listed in observations.json."""
import datetime as dt
import json
import os
from pathlib import Path
import time
from urllib.parse import urlsplit

import certifi
import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.vrt import WarpedVRT
import requests

ROOT = Path(__file__).resolve().parent
DATA = Path(os.environ.get("GREENLAND_CACHE", ROOT / "data"))
OBS = json.loads((ROOT / "observations.json").read_text())
WEST, SOUTH, EAST, NORTH = 601200, 7443600, 614400, 7451400
SCALE = {"landsat": 30, "s2": 10, "s1": 20}
TOKENS = {}


def asset_url(href):
    parsed = urlsplit(href)
    if ".blob.core.windows.net" not in parsed.hostname:
        return href
    account = parsed.hostname.split(".")[0]
    container = parsed.path.split("/")[1]
    key = (account, container)
    now = dt.datetime.now(dt.timezone.utc)
    if key not in TOKENS or TOKENS[key][0] <= now:
        address = f"https://planetarycomputer.microsoft.com/api/sas/v1/token/{account}/{container}"
        while True:
            response = requests.get(address)
            if response.status_code == 429 and "Retry-After" in response.headers:
                time.sleep(float(response.headers["Retry-After"]))
                continue
            response.raise_for_status()
            result = response.json()
            TOKENS[key] = (dt.datetime.fromisoformat(result["msft:expiry"].replace("Z","+00:00")),
                           result["token"])
            break
    return href + "?" + TOKENS[key][1]


def product_path(obs):
    folder = "radar" if obs["instrument"] == "s1" else "fine"
    return DATA / folder / "north" / (obs["id"] + ".npz")


def fetch(obs):
    dest = product_path(obs)
    if dest.exists():
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    step = SCALE[obs["instrument"]]
    radar = obs["instrument"] == "s1"
    arrays = {}
    for key, href in obs["assets"].items():
        with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
                          GDAL_HTTP_MERGE_CONSECUTIVE_RANGES="YES", CURL_CA_BUNDLE=certifi.where()):
            with rasterio.open(asset_url(href)) as src, WarpedVRT(
                src, crs="EPSG:32622", transform=from_origin(WEST,NORTH,step,step),
                width=(EAST-WEST)//step, height=(NORTH-SOUTH)//step,
                resampling=Resampling.average if radar else Resampling.nearest,
                nodata=-32768 if radar else 0,
            ) as vrt:
                arrays[key] = vrt.read(1)
    temp = dest.with_suffix(".partial.npz")
    np.savez_compressed(temp, **arrays)
    temp.replace(dest)
    print(obs["id"], flush=True)


if __name__ == "__main__":
    for observation in OBS:
        fetch(observation)
