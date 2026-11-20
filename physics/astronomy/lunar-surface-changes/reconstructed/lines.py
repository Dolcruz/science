"""Read contiguous native image-line ranges from PDS for independent terrain checks."""
from pathlib import Path
import re
import numpy as np
import requests

def get_range(url, start, stop, cache):
    name = f"{url.split('/')[-1]}.{start}-{stop}"
    path = cache /name
    if not path.exists():
        r = requests.get(url,headers={"Range": f"bytes={start}-{stop}"})
        r.raise_for_status()
        if r.status_code != 206 or not r.headers.get("Content-Range","").startswith(f"bytes {start}-{stop}/") or len(r.content)!=stop-start+1:
            raise ValueError(f"Unexpected response for {name}")
        tmp=path.with_suffix(".part")
        tmp.write_bytes(r.content)
        tmp.replace(path)
    return path.read_bytes()

class Lines:
    def __init__(self, meta, cache):
        self.meta=meta
        self.cache=cache
        self.cache.mkdir(parents=True,exist_ok=True)
        self.url=meta['original']
        self.label=get_range(self.url,0,9999,cache)
        def field(key):
            return int(re.search(rb"^\s*"+key+rb"\s*=\s*(\d+)",self.label,re.M)[1])
        self.offset=(field(rb"\^IMAGE")-1)*field(b"RECORD_BYTES")
        self.width=field(b"LINE_SAMPLES")
        if (field(b"LINES"),self.width)!=(meta["lines"],meta["samples"]):
            raise ValueError("Dimensions in PDS label differ from the product record")
    def __getitem__(self, key):
        rows,cols=key
        nbytes=self.width*2
        block=get_range(self.url,self.offset+rows.start*nbytes,self.offset+rows.stop*nbytes-1,self.cache)
        return np.frombuffer(block,dtype='<i2').reshape(-1,self.width)[:,cols]
