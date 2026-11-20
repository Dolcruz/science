"""Extract registered image cutouts and independently check local measurements."""
import csv
import os
from pathlib import Path
import sys

for variable in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[variable] = "4"
import numpy as np

ROOT = Path(__file__).resolve().parent
SITES = {"NW": (229, 360), "NNE": (665, 359), "old_pit_control": (237, 390)}
EPOCHS = [
    ("pre18", "2018-02-20"), ("pre10", "2010-12-09"),
    ("pre_west", "2019-03-22"), ("postM", "2025-12-25"),
    ("postH", "2026-01-22"), ("post_west", "2026-07-30"),
    ("post_east", "2026-07-17"), ("postA", "2025-11-28"),
]


def extract():
    out = {}
    for file, names in [
        ("registered.npz", ["pre10", "pre18", "postA", "postM", "postH", "dtm"]),
        ("opposing-relief.npz", ["pre_west", "pre_albedo", "post_west", "post_east"]),
    ]:
        with np.load(ROOT / file) as data:
            for key in names:
                frame = data[key]
                for site, (x, y) in SITES.items():
                    out[f"{site}_{key}"] = frame[y-32:y+33, x-32:x+33].copy()
    np.savez_compressed(ROOT / "candidate-chips.npz", **out)


def audit():
    yy, xx = np.mgrid[-32:33, -32:33]
    radius = np.hypot(xx, yy)
    with (ROOT / "lobe-contrasts.csv").open(encoding="utf8") as stream:
        expected = {(r["site"], r["epoch"][:10]): float(r["left_right_log_ratio"])
                    for r in csv.DictReader(stream)}
    rows = []
    shifts = []
    with np.load(ROOT / "candidate-chips.npz") as chips:
        for site in SITES:
            gap = 2 if site == "NW" else 3
            for key, date in EPOCHS:
                a = chips[f"{site}_{key}"]
                west = a[(abs(yy) <= 1) & (abs(xx + gap) <= 1)].mean()
                east = a[(abs(yy) <= 1) & (abs(xx - gap) <= 1)].mean()
                np.testing.assert_allclose(np.log(west / east), expected[site, date], atol=2e-6)
                if site == "NW":
                    values = []
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            west = a[(abs(yy-dy) <= 1) & (abs(xx-dx+gap) <= 1)].mean()
                            east = a[(abs(yy-dy) <= 1) & (abs(xx-dx-gap) <= 1)].mean()
                            values.append(float(np.log(west/east)))
                    shifts.append({"date": date, "minimum": min(values), "maximum": max(values)})
            for key in ("pre_albedo", "postA"):
                a = chips[f"{site}_{key}"]
                ratio = a[radius <= 3].mean() / np.median(a[(radius >= 13) & (radius <= 21)])
                rows.append({"site": site, "date": {"pre_albedo":"2022-04-09", "postA":"2025-11-28"}[key],
                             "center_to_local_median": float(ratio)})
        dtm = chips["NW_dtm"].astype(float)
        design = np.stack([np.ones(radius.shape), xx, yy], axis=-1)
        background = (radius > 5.5 * 1.55) & (radius < 23)
        plane = np.linalg.lstsq(design[background], dtm[background], rcond=None)[0]
        relief = dtm - design @ plane
        dtm_contrast = (np.median(relief[radius < .31 * 5.5]) -
                        np.median(relief[(radius >= .8*5.5) & (radius <= 1.3*5.5)]))
        print(f"Published DTM, NW center minus annulus: {dtm_contrast:+.4f} m")
    with (ROOT / "center-shift-sensitivity.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(shifts[0]))
        writer.writeheader()
        writer.writerows(shifts)
    with (ROOT / "albedo.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with (ROOT / "stereo-apertures.csv").open() as stream:
        expected_z = {r["method"]: float(r["center_minus_annulus"])
                      for r in csv.DictReader(stream) if r["site"] == "NW" and r["window"] == "7"}
    with np.load(ROOT / "stereo-apertures.npz") as stereo:
        for pair, value in expected_z.items():
            h = stereo[f"NW_{pair}"]
            y, x = np.indices(h.shape) - 23
            r = np.hypot(x, y)
            rel = np.nanmedian(h[r < .31 * 5.5]) - np.nanmedian(h[(r >= .8*5.5) & (r <= 1.3*5.5)])
            np.testing.assert_allclose(rel, value, atol=1e-6)
    print("Verified 24 image contrasts and three NW stereo aperture measurements.")
    for row in rows[:2]:
        print(f"NW center-to-annulus brightness, {row['date']}: {row['center_to_local_median']:.4f}")


if __name__ == "__main__":
    if "--extract" in sys.argv:
        extract()
    audit()
