"""Distances from the western limb surface change to dated flash and hardware records."""
import csv
from datetime import date
from hashlib import sha256
from io import BytesIO
import json
from math import asin, cos, radians, sin, sqrt
from pathlib import Path
import struct
from urllib.request import urlopen
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parent
LAT, LON = -6.10273, 276.99227
FIRST, LAST = "2022-11-10", "2023-03-13"
HARDWARE = ("https://pds.lroc.im-ldi.com/data/LRO-L-LROC-5-RDR-V1.0/"
            "LROLRC_2001/EXTRAS/SHAPEFILE/ANTHROPOGENIC_OBJECTS/ANTHROPOGENIC_OBJECTS_360.ZIP")


def separation(lat, lon):
    u = sin(radians(float(lat) - LAT) / 2)**2
    v = cos(radians(float(lat))) * cos(radians(LAT)) * sin(radians(float(lon) - LON) / 2)**2
    return 3474.8 * asin(min(1, sqrt(u + v)))


def hardware(raw):
    with ZipFile(BytesIO(raw)) as archive:
        db = archive.read(next(x for x in archive.namelist() if x.upper().endswith(".DBF")))
    n, header, stride = struct.unpack_from("<IHH", db, 4)
    fields = [(db[i:i+11].split(b"\0")[0].decode(), db[i+16]) for i in range(32,header-1,32)]
    rows = []
    for i in range(n):
        record = db[header+i*stride:header+(i+1)*stride]
        pos = 1
        data = {}
        for key, width in fields:
            data[key] = record[pos:pos+width].decode("latin1").strip()
            pos += width
        rows.append(data)
    return rows


def run():
    flashes = list(csv.DictReader((ROOT / "liakos-events.csv").open()))
    for row in flashes:
        assert abs(separation(row["lat"],row["lon"])-float(row["distance_km"])) < 1.e-6
    in_window = [r for r in flashes if FIRST <= r["date"] <= LAST]
    nearest = min(in_window, key=lambda r: float(r["distance_km"]))
    close = next(r for r in flashes if r["n"]=="283")
    with urlopen(HARDWARE) as f:
        raw = f.read()
    objects = hardware(raw)
    in_range = [o["OBJECT_ID"] for o in objects if FIRST.replace("-","") <= o["DATE"] <= LAST.replace("-","")]
    report = dict(center_lat=LAT,center_lon_east=LON,start_utc_date=FIRST,end_utc_date=LAST,
                  in_window_liakos=len(in_window),nearby_excluded=dict(event_id=283,distance_km=separation(close["lat"],close["lon"]),
                  days_after_end=(date.fromisoformat(close["date"])-date.fromisoformat(LAST)).days),
                  closest_in_window_neliota=nearest,
                  january_26_2023_uai_km=separation(23.79,-31.36),
                  february_23_2023_distance_to_ideler_l_landmark_km=separation(-49.33,23.65),
                  pds_hardware=dict(rows=len(objects),source_sha256=sha256(raw).hexdigest(),url=HARDWARE,
                                    in_window_ids=in_range,years_2022_2023=[
                                         dict(name=o["SHORT_NAME"],date=o["DATE"],lat=o["LATITUDE"],lon=o["LON_360"])
                                         for o in objects if o["DATE"].startswith(("2022","2023"))]))
    (ROOT/"summary.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))


if __name__ == "__main__":
    run()
