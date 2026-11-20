"""Register the underlying NAC images and survey their full common footprint."""
import os
for variable in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[variable] = "4"

import argparse
import json
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
import registration as scan

B = "M186762974RC"
A = "M1148028911RC"

def setup():
    scan.META = json.loads((HERE / "observations.json").read_text())
    scan.REF = A
    scan.GRID = 1.05
    scan.ORIGIN = np.array([225.97095, -7.30832])
    scan.SCALE = np.array([scan.DEG * np.cos(np.deg2rad(scan.ORIGIN[1])), -scan.DEG])
    cv2.setNumThreads(4)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    setup()
    (args.out / "validation").mkdir(parents=True, exist_ok=True)
    scan.scan_pair(scan.Frame(B, args.raw), scan.Frame(A, args.raw), args.out)
