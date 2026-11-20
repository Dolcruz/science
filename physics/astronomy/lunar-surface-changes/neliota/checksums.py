"""Download and verify the five original LROC NAC products for the survey."""
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
