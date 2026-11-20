"""Check the report's central measurements from the distributed image arrays and tables."""
import csv
from datetime import date
from hashlib import sha256
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent


def rows(path):
    with (ROOT / path).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def check_files():
    lines = (ROOT / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()
    for line in lines:
        expected, name = line.split("  ", 1)
        if sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise ValueError(f"Checksum differs for {name}")
    print(f"Verified SHA-256 for {len(lines)} files.")


def mcgetchin():
    contrasts = []
    with np.load(ROOT / "mcgetchin/candidate-chips.npz") as data:
        for epoch in ("pre10", "postH", "pre_west", "post_west"):
            chip = data[f"NW_{epoch}"]
            west = chip[31:34, 29:32].mean()
            east = chip[31:34, 33:36].mean()
            contrasts.append(np.log(west / east))
    np.testing.assert_allclose(contrasts, [-.053, .707, .451, -.995], atol=.00051)
    heights = []
    with np.load(ROOT / "mcgetchin/stereo-apertures.npz") as stereo:
        for pair in ("EW", "EN", "NW"):
            image = stereo[f"NW_{pair}"]
            y, x = np.indices(image.shape) - 23
            radius = np.hypot(x, y)
            center = np.nanmedian(image[radius < .31 * 5.5])
            ring = np.nanmedian(image[(radius >= 4.4) & (radius <= 7.15)])
            heights.append(center - ring)
    np.testing.assert_allclose(heights, [-.37, -.51, -.44], atol=.005)
    field = rows("independent-relief/far-field-relief.csv")
    west_5m = [float(row["west_5m"]) for row in field
               if row["model"] in ("EW", "EN", "NW") and float(row["inner"]) == 12 and float(row["outer"]) == 18]
    np.testing.assert_equal(len(west_5m), 3)
    np.testing.assert_allclose([min(west_5m), max(west_5m)], [.57, .78], atol=.005)
    print("McGetchin west/east log contrasts:", *np.round(contrasts, 3))
    print("Seven-pixel stereo center minus surrounding ring (m):", *np.round(heights, 3))


def flash_field():
    y, x = np.indices((81, 81)) - 40
    radius = np.hypot(x, y)
    def contrast(chip):
        return np.log(chip[radius <= 2.5]).mean() - np.median(np.log(chip[(radius >= 7) & (radius <= 15)]))
    with np.load(ROOT / "neliota/283/check-24/chips.npz") as images:
        change = 100 * np.expm1(contrast(images["M1491897245LC"]) - contrast(images["M1405157120RC"]))
    np.testing.assert_allclose(change, 29.78, atol=.005)
    y, x = np.indices((151, 151)) - 75
    radius = np.hypot(x, y)
    before, after = "M1422745700LC", "M1433308510RC"
    with np.load(ROOT / "nel283-shape/cutouts.npz") as images:
        log_core = []
        for name in (before, after):
            chip = images[name]
            bg = chip[(radius >= 13) & (radius <= 25)].mean()
            log_core.append(np.log((chip / bg)[radius <= 3].mean()))
    np.testing.assert_allclose(log_core, [-.003218, .220567], atol=.000002)
    records = {row["product"]: date.fromisoformat(row["date"]) for row in rows("nel283-shape/contrast.csv")}
    days = (date(2023, 5, 25) - records[after]).days
    np.testing.assert_equal(days, 73)
    print(f"Field 283 brightness increase: {change:.2f}%. Image interval {records[before]} to {records[after]}, {days} days before the flash.")


if __name__ == "__main__":
    check_files()
    mcgetchin()
    flash_field()
