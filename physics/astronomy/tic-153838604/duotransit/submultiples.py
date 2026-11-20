"""Test constant-depth submultiples of the measured 56.07936-day recurrence."""
import argparse
import csv
from pathlib import Path

import numpy as np

from measure import DURATION, FIRST, SECOND, read_sector


def depth_at(time, flux, centre, cadence):
    # Search sorted endpoints directly to handle open intervals consistently.
    def interval(low, high):
        left = np.searchsorted(time, centre + low, side="right")
        right = np.searchsorted(time, centre + high, side="left")
        data = flux[left:right]
        return np.median(data) if len(data) >= .70 * (high - low) / cadence else np.nan
    core = interval(-.30*DURATION, .30*DURATION)
    baseline = (interval(-1.8*DURATION, -.65*DURATION) +
                interval(.65*DURATION, 1.8*DURATION)) / 2
    return 1000 * (1 - core / baseline)


def maximum_contrast(time, flux, cadence, start, finish):
    # The selected observations change only at these six translated cadence times.
    # Evaluate boundaries, adjacent floating-point values and one interior point per cell.
    edges = [time - off*DURATION for off in (-1.8, -.65, -.30, .30, .65, 1.8)]
    boundaries = np.unique(np.concatenate(([start, finish], *edges)))
    boundaries = boundaries[(boundaries >= start) & (boundaries <= finish)]
    trials = np.unique(np.concatenate((boundaries, np.nextafter(boundaries, -np.inf),
                                       np.nextafter(boundaries, np.inf),
                                       (boundaries[:-1]+boundaries[1:])/2)))
    values = np.array([depth_at(time, flux, c, cadence) for c in trials])
    return float(np.max(values)) if np.isfinite(values).all() else np.nan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=Path("fits"))
    parser.add_argument("--output", type=Path, default=Path("."))
    args = parser.parse_args()
    with (args.output/"measurements.csv").open(encoding="utf-8") as stream:
        events = list(csv.DictReader(stream))
    catalogue_aliases = []
    for count in range(1, 20):
        trial_period = (SECOND - FIRST) / count
        row = {"elapsed_cycles": count, "period_days": trial_period}
        for event in events[-2:]:
            delta = float(event["fitted_btjd"]) - FIRST
            nearest = round(delta / trial_period)
            row[f"sector_{event['sector']}_miss_days"] = abs(delta - nearest * trial_period)
        catalogue_aliases.append(row)
    with (args.output/"catalogue_aliases.csv").open("w", newline="", encoding="utf-8") as out:
        writer = csv.DictWriter(out, fieldnames=catalogue_aliases[0])
        writer.writeheader()
        writer.writerows(catalogue_aliases)
    p, t0 = np.polyfit([float(r["cycle"]) for r in events],
                      [float(r["fitted_btjd"]) for r in events],1)
    sectors = {}
    for s in [97,98]:
        time, flux, _, cadence, _, _ = read_sector(s,args.cache)
        sectors[s] = time, flux, cadence
    # Any period ≤ 3.1 days must produce at least one event in this interval.
    start, finish = 3997., 4000.1
    bound = maximum_contrast(*sectors[98],start,finish)
    print(f"Continuous {finish-start:.1f}-day window S98 [{start}, {finish}]: {bound:.4f} ppt")
    rows = []
    for divisor in range(2,int(np.ceil(p / (finish-start)))):
        shorter = p/divisor
        candidates = []
        for s,(time,flux,cadence) in sectors.items():
            for j in range(int(np.ceil((time[0]-t0)/shorter)),int(np.floor((time[-1]-t0)/shorter))+1):
                if j % divisor == 0:
                    continue
                centre = t0 + j*shorter
                quickly = depth_at(time,flux,centre,cadence)
                if np.isfinite(quickly):
                    candidates.append((abs(quickly),s,centre))
        for _,s,centre in sorted(candidates):
            # A ±30 min allowance exceeds the four-event residuals.
            bound_local = maximum_contrast(*sectors[s],centre-1/48,centre+1/48)
            if np.isfinite(bound_local) and bound_local < 4:
                rows.append(dict(divisor=divisor,period_days=shorter,sector=s,
                                 predicted_btjd=centre,max_contrast_ppt=bound_local))
                break
        else:
            raise RuntimeError(f"No covered non-detection for divisor {divisor}")
    with (args.output/"submultiples.csv").open("w", newline="", encoding="utf-8") as out:
        w=csv.DictWriter(out,fieldnames=rows[0]); w.writeheader();w.writerows(rows)
    print(f"Divisors {rows[0]['divisor']}–{rows[-1]['divisor']}: worst upper contrast = "
          f"{max(r['max_contrast_ppt'] for r in rows):.4f} ppt")

if __name__ == "__main__":
    main()
