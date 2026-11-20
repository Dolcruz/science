"""Locate the two sites on the published 950 m geomorphic map."""
from io import BytesIO
from pathlib import Path
import os

import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt
import numpy as np
from PIL import Image
import requests

ROOT = Path(__file__).resolve().parent
DATA = Path(os.environ.get("MCGETCHIN_DATA", ROOT / "data"))
FIGURE = "https://cdn.ncbi.nlm.nih.gov/pmc/blobs/6846/13580579/09403411384f/sciadv.aeh7812-f7.webp"
SITES = {"NW": (229, 360), "NNE": (665, 359)}


def main():
    path = DATA / "publication-figure7.webp"
    if path.exists():
        image = np.asarray(Image.open(path).convert("RGB"))
    else:
        response = requests.get(FIGURE)
        response.raise_for_status()
        image = np.asarray(Image.open(BytesIO(response.content)).convert("RGB"))
    scale = 1594 / 950
    x0 = y0 = 800
    fig, axes = plt.subplots(1, 2, figsize=(8.4, 4.6), layout="constrained")
    for ax, (name, (x, y)) in zip(axes, SITES.items()):
        cx, cy = x0 + (x-600)*scale, y0 + (y-600)*scale
        r = 80
        xmin, ymin = round(cx)-r, round(cy)-r
        patch = image[ymin:ymin+2*r+1, xmin:xmin+2*r+1]
        ax.imshow(patch, extent=[(xmin-cx-.5)/scale, (xmin-cx+2*r+.5)/scale,
                                 (ymin-cy+2*r+.5)/scale, (ymin-cy-.5)/scale])
        ax.plot(0, 0, 'o', mfc='none', mec='#008568', mew=2, ms=9)
        ax.set_xlabel("East offset (m)")
        ax.set_ylabel("South offset (m)")
        ax.set_title({"NW":"Northwestern site", "NNE":"Northern site"}[name])
        # Color identifies the interior of a boulder symbol, not its center.
        rgb = image[:1597, :1597].astype(float)
        yy, xx = np.where(np.ptp(rgb, axis=2) > 55)
        print(f"{name}: nearest colored symbol pixel {np.min(np.hypot(xx-cx, yy-cy))/scale:.1f} m")
    fig.suptitle("Site positions on the published geomorphic map", fontsize=15)
    fig.supxlabel("Green rings mark the sampled centers. Map adapted from Robinson et al. (2026), Fig. 7, CC BY 4.0.", fontsize=8)
    fig.savefig(ROOT / "published-map.png", dpi=165)
    plt.close(fig)


if __name__ == "__main__":
    main()
