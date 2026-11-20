"""Match each Bochum light-curve time to its nearest same-filter observatory frame."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def read_rows(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def main():
    curves = read_rows(ROOT.parent / "bochum-curves.csv")
    frames = read_rows(ROOT / "frames.csv")
    for band in ("r", "i"):
        times = sorted({float(row["mjd_utc"]) for row in curves if row["band"] == band})
        image_times = [float(row["dateObs"]) for row in frames
                       if row["bandpassId"] == f"SDSS {band}'" and row["field"] == "GDS_0734-2011"]
        matched = [min(image_times, key=lambda frame: abs(frame - epoch)) for epoch in times]
        if len(set(matched)) != len(times):
            raise ValueError("Multiple light-curve epochs matched the same frame")
        max_delta = max(abs(frame - epoch) * 86400 for frame, epoch in zip(matched, times))
        print(f"{band}: {len(times)} distinct frames, maximum difference {max_delta:.3f} s")
        if max_delta >= 0.5:
            raise ValueError("Frame match is outside the reported half-second agreement")


if __name__ == "__main__":
    main()
