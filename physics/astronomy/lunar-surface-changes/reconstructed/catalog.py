"""Crossmatch a lunar position against published crater and splotch coordinates."""
import csv
import io
import json
from math import asin, cos, radians, sin, sqrt
from pathlib import Path
import struct
import zipfile

import argparse
import hashlib
import requests


HERE=Path(__file__).resolve().parent
DATA=None

def archive_rows():
    with zipfile.ZipFile(DATA / "lroc-new-craters-360.zip") as z:
        data = z.read("GLOBAL_NEW_CRATERS_360.DBF")
    n, header, stride = struct.unpack_from("<IHH",data,4)
    fields=[(data[k:k+11].split(b"\0")[0].decode(),data[k+16]) for k in range(32,header-1,32)]
    for i in range(n):
        line=data[header+i*stride:header+(i+1)*stride]
        assert line[0:1] == b" "
        row={}
        position=1
        for key,width in fields:
            row[key]=line[position:position+width].decode().strip()
            position+=width
        yield i+1,row


def csv_rows(file):
    return csv.DictReader(io.StringIO((DATA/file).read_bytes().decode("utf-8-sig").replace("\r\r\n","\n")))


def entries():
    for i,row in archive_rows():
        yield "LROC 2016 new craters",str(i),row["lat"],row["lon"],row["diam_m"]
    prefix="Sokolowska_etal_2025_PCC-"
    for row in csv_rows(prefix+"Craters.csv"):
        if row["Crater ID"]:
            yield "Sokolowska 2025 craters",row["Crater ID"],row["exact lat [deg]"],row["exact lon [deg]"],row["measured diameter [m]"]
    for row in csv_rows(prefix+"Splotches.csv"):
        yield "Sokolowska 2025 splotches",row["Impact Splotch ID"],row["exact lat [deg]"],row["exact lon [deg]"],""
    for row in csv_rows(prefix+"Craters-Not-Found.csv"):
        yield "Sokolowska 2025 approximate unlocated",row["Crater ID"],row["approximate latitude"],row["approximate longitude"],""
    for row in csv_rows("newCraterColdSpotCatalog.csv"):
        yield "Powell 2026 recent large craters",row["index"],row["latitude"],row["longitude"],row["diameter_m"]
    for i,row in enumerate(csv_rows("globalColdSpotCatalog.csv"),1):
        yield "Powell 2026 global cold spots",str(i),row["latitude"],row["longitude"],row["diameter_m"]


def main(folder, target_lon, target_lat, output):
    global DATA
    DATA=folder
    DATA.mkdir(parents=True,exist_ok=True)
    for source in csv.DictReader((HERE/"catalog-sources.csv").open()):
        f=DATA/source["file"]
        if not f.exists():
            r=requests.get(source["url"]);r.raise_for_status()
            if hashlib.sha256(r.content).hexdigest()!=source["sha256"]:raise ValueError(f"Source checksum changed for {f.name}")
            f.write_bytes(r.content)
        if hashlib.sha256(f.read_bytes()).hexdigest()!=source["sha256"]:raise ValueError(f"Unexpected checksum for {f.name}")
    rows={}
    for source,ident,lat,lon,diam in entries():
        if not lat or not lon:continue
        a,b=float(lat),float(lon)
        chord=sin(radians(a-target_lat)/2)**2+cos(radians(a))*cos(radians(target_lat))*sin(radians(b-target_lon)/2)**2
        dist=3474.8*asin(sqrt(min(1.,chord)))
        rows.setdefault(source,[]).append((dist,ident,a,b))
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['catalog','coordinate_rows','nearest_id','nearest_lat_deg','nearest_lon_deg','distance_km'])
        for source,group in rows.items():
            dist,n,a,b=min(group);w.writerow([source,len(group),n,a,b,dist])

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("folder",type=Path);p.add_argument("longitude",type=float);p.add_argument("latitude",type=float);p.add_argument("output",type=Path)
    q=p.parse_args();main(q.folder,q.longitude,q.latitude,q.output)
