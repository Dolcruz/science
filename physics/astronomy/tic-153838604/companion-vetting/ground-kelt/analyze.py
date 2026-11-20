"""KELT night-level tests of the two fixed TESS phases."""
import csv
import json
from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
EPOCH = 2458447.10503234
PERIOD = 56.07935938
DURATION_H = 2.61


def load(processing):
    frames = []
    for path in sorted(HERE.glob(f"*_{processing}_lc.tbl")):
        rows = "".join(line for line in path.read_text().splitlines(True) if line.startswith(" "))
        data = pd.read_csv(StringIO(rows), sep=r"\s+", names=["bjd", "mag", "err"])
        data["pier"] = "east" if "_east_" in path.name else "west"
        frames.append(data)
    data = pd.concat(frames, ignore_index=True).sort_values("bjd")
    data["night"] = np.floor(data.bjd).astype(int)  # BJD changes integer near local afternoon
    return data


def contrast(magnitudes, mask):
    return 1000 * (magnitudes[mask].mean() - magnitudes[~mask].mean())


def test(data, phase, shift_minutes, processing):
    ref = EPOCH + phase * PERIOD + shift_minutes / 1440
    offset = (data.bjd - ref + PERIOD / 2) % PERIOD - PERIOD / 2
    in_box = abs(offset) <= DURATION_H / 48
    covered = data[in_box]
    assert covered.night.nunique() == 1
    event_night = int(covered.night.iloc[0])
    event = data[data.night == event_night]
    by_pier = []
    controls = []
    for pier, visits in event.groupby("pier"):
        mask = in_box.loc[visits.index].to_numpy()
        if not (mask.any() and (~mask).any()):
            continue
        observed = contrast(visits.mag.to_numpy(), mask)
        placebo = []
        for night, sample in data[data.pier == pier].groupby("night"):
            if night == event_night or len(sample) < len(visits):
                continue
            # The east sequence ends, and the west sequence starts, at the meridian flip.
            match = sample.tail(len(visits)) if pier == "east" else sample.head(len(visits))
            delta = contrast(match.mag.to_numpy(), mask)
            placebo.append(delta)
            controls.append([processing, phase, shift_minutes, pier, int(night), delta,
                             24 * (match.bjd.max() - match.bjd.min())])
        q = np.quantile(placebo, [0, .025, .16, .5, .84, .975, 1])
        by_pier.append(dict(pier=pier, n_in=int(mask.sum()), n_out=int((~mask).sum()),
                            observed_delta_mmag=float(observed), control_nights=len(placebo),
                            control_quantiles_mmag=q.tolist(),
                            contrast_minus_control_median_mmag=float(observed - q[3]),
                            empirical_95_interval_mmag=[float(observed-q[5]), float(observed-q[1])],
                            one_sided_rank_p=(1+sum(x >= observed for x in placebo))/(1+len(placebo))))
    return dict(phase=phase, shift_minutes=shift_minutes, night_integer_bjd=event_night,
                epoch_number=int(np.rint((covered.bjd.mean()-ref) / PERIOD)),
                n_exposures=int(in_box.sum()), by_pier=by_pier), controls


def main():
    result = {}
    controls = []
    for processing in ["tfa", "raw"]:
        data = load(processing)
        measurements = []
        for phase in [0., .5]:
            for shift in [0, -10, 10]:
                observation, reference = test(data, phase, shift, processing)
                measurements.append(observation)
                controls.extend(reference)
        result[processing] = dict(exposures=len(data), nights=int(data.night.nunique()),
                                  bjd_range=[data.bjd.min(), data.bjd.max()], tests=measurements)
    (HERE / "kelt-result.json").write_text(json.dumps(result, indent=2) + "\n")
    with (HERE / "night-controls.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["processing", "phase", "shift_minutes", "pier", "night_integer_bjd",
                         "contrast_mmag", "comparison_sequence_duration_h"])
        writer.writerows(controls)


if __name__ == "__main__":
    main()
