"""Measure east–west parallax at the NW site using the two published orthophotos.

Run fetch.py to obtain the GeoTIFFs, then run this script. Use --data DIRECTORY
or MCGETCHIN_DATA to select an existing extracted dataset. Heights are local
stereo residuals, in metres. The table compares the central disk with its annulus.
"""
import argparse
import json
import os
from pathlib import Path

for variable in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "BLIS_NUM_THREADS"):
    os.environ[variable] = "4"

import cv2
import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates


ROOT = Path(__file__).resolve().parent
ORTHOPHOTOS = (
    "NAC_DTM_NEW200CRAT3_M1521338586_100cm_crop.tif",
    "NAC_DTM_NEW200CRAT3_M1521352616_100cm_crop.tif",
)


def read_site(path):
    """Bilinearly sample the published GeoTIFF on the north-up 1 m grid."""
    row, col = np.mgrid[-52:53, -52:53]
    east = -3421266.0 + 229 + col + 0.5
    north = 41646.0 - 360 - row - 0.5
    with Image.open(path) as source:
        x0, y0 = source.tag_v2[33922][3:5]
        dx, dy = source.tag_v2[33550][:2]
        pixel = [(y0 - north) / dy - 0.5, (east - x0) / dx - 0.5]
        values = map_coordinates(np.asarray(source, dtype=float), pixel, order=1)
    if not np.all(np.isfinite(values) & (values > 0)):
        raise ValueError(f"Missing or nonpositive radiometry in {path.name}")
    return np.log(values).astype("float32")


def disparity_per_metre(metadata):
    """Linearized disparity for one metre of relief, in east/south grid pixels."""
    lat, lon = np.radians([1.36151, 67.16426])
    east = np.array([-np.sin(lon), np.cos(lon), 0])
    north = np.array([-np.sin(lat)*np.cos(lon), -np.sin(lat)*np.sin(lon), np.cos(lat)])
    up = np.cross(east, north)
    projections = []
    for side in ("E", "W"):
        geometry = metadata[side]
        lat_s, lon_s = np.radians([geometry["sub_lat"], geometry["sub_lon"]])
        radial = np.array([np.cos(lat_s)*np.cos(lon_s), np.cos(lat_s)*np.sin(lon_s), np.sin(lat_s)])
        spacecraft = (1737.4 + geometry["altitude_km"]) * radial
        # Mean lunar radius, with the local reference elevation of -0.846 km.
        height = spacecraft @ up - (1737.4 - 0.846)
        projections.append(np.array([-spacecraft @ east, spacecraft @ north]) / height)
    return projections[1] - projections[0]


def measure(images, baseline, width):
    """Compute two-dimensional normalized correlation and fit its subpixel peak."""
    half = width // 2
    y, x = np.mgrid[-23:24, -23:24]
    radius = np.hypot(x, y)
    heights = np.full(x.shape, np.nan)
    search = 3
    v, u = np.mgrid[-1:2, -1:2]
    quadratic = np.stack([np.ones_like(u), u, v, u*u, u*v, v*v], axis=-1).reshape(9, 6)
    for i, j in np.ndindex(heights.shape):
        row, col = 52 + y[i, j], 52 + x[i, j]
        template = images[0][row-half:row+half+1, col-half:col+half+1]
        margin = half + search
        area = images[1][row-margin:row+margin+1, col-margin:col+margin+1]
        ncc = cv2.matchTemplate(area, template, cv2.TM_CCOEFF_NORMED)
        py, px = np.unravel_index(np.argmax(ncc), ncc.shape)
        if min(py, px, 2*search-py, 2*search-px) == 0 or ncc[py, px] < 0.65:
            continue
        patch = ncc[py-1:py+2, px-1:px+2]
        c = np.linalg.lstsq(quadratic, patch.ravel(), rcond=None)[0]
        hessian = np.array([[2*c[3], c[4]], [c[4], 2*c[5]]])
        if np.linalg.eigvalsh(hessian)[-1] >= 0:
            continue
        offset = np.linalg.solve(hessian, -c[1:3])
        if np.abs(offset).max() > 1:
            continue
        shift = np.array([px-search, py-search]) + offset
        heights[i, j] = (shift @ baseline) / (baseline @ baseline)

    background = (radius > 8.525) & (radius < 23) & np.isfinite(heights)
    plane = np.stack([np.ones_like(x), x, y], axis=-1)
    fit = np.linalg.lstsq(plane[background], heights[background], rcond=None)[0]
    residual = heights - plane @ fit
    center = residual[radius < 1.705]
    annulus = residual[(radius >= 4.4) & (radius <= 7.15)]
    return np.isfinite(center).sum(), np.nanmedian(center) - np.nanmedian(annulus)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path(os.environ.get("MCGETCHIN_DATA", ROOT / "data")))
    args = parser.parse_args()
    cv2.setNumThreads(4)
    images = [read_site(args.data / filename) for filename in ORTHOPHOTOS]
    baseline = disparity_per_metre(json.loads((ROOT / "stereo-geometry.json").read_text()))
    print("window_px,valid_center_pixels,center_minus_annulus_m")
    for width in (5, 7, 9, 11, 15):
        count, contrast = measure(images, baseline, width)
        print(f"{width},{count},{contrast:+.4f}")


if __name__ == "__main__":
    main()
