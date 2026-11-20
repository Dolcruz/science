"""Download and verify the two full LROC NAC products used for the field survey."""
import argparse
from hashlib import md5
import json
from pathlib import Path
import re
import requests

BASE=Path(__file__).resolve().parent


def verify(path):
    with path.open("rb") as f:
        label=f.read(10000)
        def field(k):
            return int(re.search(rb"^\s*"+re.escape(k)+rb"\s*=\s*(\d+)",label,re.M).group(1))
        record=field(b"RECORD_BYTES")
        expected=re.search(rb'MD5_CHECKSUM\s*=\s*"(\w+)"',label).group(1).decode()
        if path.stat().st_size!=record*field(b"FILE_RECORDS"):
            raise ValueError(f"Incomplete file: {path}")
        f.seek((field(b"^IMAGE")-1)*record)
        digest=md5()
        while block:=f.read(2**22):
            digest.update(block)
        if digest.hexdigest()!=expected:raise ValueError(f"Pixel checksum failure: {path}")
        return expected


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("folder",type=Path);args=p.parse_args()
    args.folder.mkdir(exist_ok=True,parents=True)
    for name in ["M186762974RC","M1148028911RC"]:
        m=json.loads((BASE/"observations.json").read_text())[name]
        dest=args.folder/(name+".IMG")
        if not dest.is_file():
            tmp=dest.with_suffix(".part")
            with requests.get(m["original"],stream=True) as resp:
                resp.raise_for_status()
                with tmp.open("wb") as f:
                    for chunk in resp.iter_content(2**20):
                        f.write(chunk)
            verify(tmp)
            tmp.replace(dest)
        print(name,verify(dest))
