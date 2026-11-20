"""Reproduce the four-event photometric ephemeris of TIC 153838604."""
import argparse
import csv
import hashlib
import io
from pathlib import Path
from urllib.request import urlopen

import numpy as np
from astropy.io import fits
from matplotlib import pyplot as plt
from scipy.optimize import least_squares

TIC = 153838604
FIRST, SECOND = 1447.10227, 2176.13853  # Hawthorn et al., Table A2
DURATION = 2.61 / 24  # days
SECTORS = [5, 32, 97, 98]
CYCLES = np.array([0, 13, 45, 46])
PERIOD = (SECOND - FIRST) / 13


def read_sector(sector, cache):
    name = f"hlsp_qlp_tess_ffi_s{sector:04}-{TIC:016}_tess_v01_llc.fits"
    url = f"https://archive.stsci.edu/hlsps/qlp/s{sector:04}/0000/0001/5383/8604/{name}"
    path = cache / name
    if not path.exists():
        with urlopen(url) as response:
            path.write_bytes(response.read())
    payload = path.read_bytes()
    with fits.open(io.BytesIO(payload)) as hd:
        assert hd[0].header["TICID"] == TIC and hd[0].header["SECTOR"] == sector
        assert hd[1].header["BJDREFI"] == 2457000 and hd[1].header["TIMESYS"] == "TDB"
        rows = hd[1].data
        name = "DET_FLUX" if "DET_FLUX" in rows.names else "KSPSAP_FLUX"
        keep = (rows["QUALITY"] == 0) & np.isfinite(rows[name]) & np.isfinite(rows["TIME"])
        arrays = [np.asarray(rows[key][keep], float) for key in ("TIME", name, "SAP_FLUX")]
        return *arrays, hd[1].header["TIMEDEL"], hashlib.sha256(payload).hexdigest(), url


def triangular_profile(x, halfwidth, exposure):
    # Antiderivative of a unit-height triangle centred at zero; integrate per cadence.
    def integral(t):
        right = np.maximum(t + halfwidth, 0)**2
        middle = np.maximum(t, 0)**2
        left = np.maximum(t - halfwidth, 0)**2
        return (right - 2 * middle + left) / (2 * halfwidth)
    return (integral(x + exposure / 2) - integral(x - exposure / 2)) / exposure


def fit_event(time, flux, centre, exposure):
    use = np.abs(time - centre) < 0.30
    x = time[use] - centre
    y = flux[use] / np.median(flux[use])
    def model(params):
        offset, slope, depth, shift, width = params
        return offset + slope*x - depth * triangular_profile(x - shift, width, exposure)
    result = least_squares(lambda params: model(params) - y,
                           [1., 0., .016, 0., DURATION / 2],
                           bounds=([.92,-1,0,-.06,.015], [1.08,1,.08,.06,.16]))
    if not result.success:
        raise ArithmeticError(result.message)
    base, slope, depth, shift, width = result.x
    return centre + shift, depth, width * 48, x, y - base - slope*x


def contrasts(time, flux, centre, cadence):
    offset = time - centre
    core = np.abs(offset) < .30 * DURATION
    left = (offset > -1.8*DURATION) & (offset < -.65*DURATION)
    right = (offset > .65*DURATION) & (offset < 1.8*DURATION)
    if any(np.sum(sel) < .7 * width / cadence for sel, width in
           [(core,.60*DURATION), (left,1.15*DURATION), (right,1.15*DURATION)]):
        return np.nan
    baseline = (np.median(flux[left]) + np.median(flux[right])) / 2
    return 1000 * (1 - np.median(flux[core]) / baseline)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=Path("fits"))
    parser.add_argument("--output", type=Path, default=Path("."))
    args = parser.parse_args()
    args.cache.mkdir(parents=True, exist_ok=True)
    args.output.mkdir(parents=True, exist_ok=True)
    figure, axes = plt.subplots(2, 2, figsize=(9, 5.7), sharex=True, sharey=True)
    measurements = []
    for sector, cycle, ax in zip(SECTORS, CYCLES, axes.ravel()):
        time, flux, raw, exposure, digest, url = read_sector(sector, args.cache)
        predicted = FIRST + cycle * PERIOD
        mid, depth, duration, x, y = fit_event(time, flux, predicted, exposure)
        core_stat = contrasts(time, flux, mid, exposure)
        raw_stat = contrasts(time, raw, mid, exposure)
        # Fixed independent comparison windows span the sector and use both sidebands.
        centres = np.arange(time.min()+2*DURATION, time.max()-2*DURATION, 4*DURATION)
        centres = centres[np.abs(centres - mid) > 4*DURATION]
        controls = np.array([contrasts(time, flux, c, exposure) for c in centres])
        controls = controls[np.isfinite(controls)]
        measurements.append(dict(sector=sector, cycle=cycle, proposed_btjd=predicted,
            fitted_btjd=mid, model_depth_ppt=depth*1000, model_duration_h=duration,
            core_depth_ppt=core_stat, raw_core_depth_ppt=raw_stat, controls=len(controls),
            max_control_ppt=max(controls,default=float('nan')),
            exceedances=int(sum(controls>=core_stat)), sha256=digest, source=url))
        ax.scatter(x*24, y*1000, s=8, c="#606c81", alpha=.60, edgecolors="none")
        line = np.linspace(-4.2, 4.2, 420)
        model = -depth * triangular_profile(line / 24 + predicted - mid, duration / 48, exposure)
        ax.plot(line, model*1000, color="#b03d35", lw=1.8)
        ax.axvline(0, color="#294e80", lw=.8, ls="--")
        ax.set_title(f"Sector {sector}     Cycle {cycle}", loc="left", fontsize=11)
        ax.set_xlim(-4.2,4.2)
        ax.grid(alpha=.16)
    best_period, epoch = np.polyfit(CYCLES,[r["fitted_btjd"] for r in measurements],1)
    for record in measurements:
        record["residual_min"] = (record["fitted_btjd"] - epoch - best_period*record["cycle"])*1440
        print(record)
    print(f"Equal-weight ephemeris: {epoch:.7f} + E × {best_period:.8f} BTJD days")
    with (args.output/"measurements.csv").open("w", newline="", encoding="utf-8") as out:
        writer=csv.DictWriter(out, fieldnames=measurements[0].keys())
        writer.writeheader()
        writer.writerows(measurements)
    figure.suptitle("TIC 153838604  |  Four transit-like events", fontsize=15, x=.10, ha="left")
    figure.supxlabel("Hours from the predicted midpoint")
    figure.supylabel("Relative flux (parts per thousand)")
    figure.tight_layout()
    figure.savefig(args.output/"four-events.png", dpi=160, bbox_inches="tight")

if __name__ == "__main__":
    main()
