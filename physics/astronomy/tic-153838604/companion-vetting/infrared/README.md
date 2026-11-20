# Infrared eclipse coverage of TIC 153838604

One NEOWISE exposure caught the predicted center of the primary eclipse. At 4.6 µm (W2), it measured **3.04% ± 2.78% less flux** than the median of 18 clean exposures from the same observing visit. Three of those 18 comparison exposures were equally faint or fainter. The observation is consistent with the optical eclipse depth of about 1.5% and with constant infrared flux. The simultaneous 3.4 µm (W1) exposure carries a transient-pixel flag, leaving the primary eclipse color undetermined. [NEOWISE final data release](https://irsa.ipac.caltech.edu/data/WISE/docs/release/NEOWISE/index.html) · [IRSA recommendations for transient-pixel flags](https://irsa.ipac.caltech.edu/data/WISE/docs/release/NEOWISE/expsup/sec2_3.html) · [Optical ephemeris and measurements](../../duotransit/README.md)

## Individual exposures

There are 614 NEOWISE exposures and 58 earlier AllWISE multiepoch measurements within 3 arcseconds of the Gaia position. Using a 2.61-hour window, one NEOWISE exposure falls within a predicted primary eclipse and three fall within a window centered halfway through the 56.0793594-day cycle. None of the 58 AllWISE measurements falls in either window. Their closest offsets are 6.07 hours from primary center and 150.68 hours from halfway. [AllWISE multiepoch data](https://irsa.ipac.caltech.edu/data/WISE/docs/release/AllWISE/expsup/sec3_2.html)

| UTC date and time | Event | Offset from center | W1 flux loss | W2 flux loss |
|---|---|---:|---:|---:|
| 17 Jan 2022 05:41:57 | Halfway | +10.27 min | −1.58 ± 2.06% | +0.96 ± 2.96% |
| 16 Jan 2023 17:57:14 | Primary, cycle 27 | +2.78 min | Flagged | **+3.04 ± 2.78%** |
| 16 Jan 2024 05:41:52 | Halfway | −35.35 min | −0.42 ± 1.77% | +1.14 ± 2.41% |
| 16 Jan 2024 07:14:50 | Halfway | +57.62 min | +1.14 ± 1.74% | −1.72 ± 2.56% |

The first row has reduced frame quality (`qi_fact = 0.5`) and is included only in the relaxed selection. The other three exposures have full frame quality. At primary, W1 carries `w1frtr = 0101`, while W2 has `w2frtr = 0000`. The W2 point is 0.0335 mag fainter than its reference. A one-sided Gaussian 95% upper limit on the **instantaneous observed W2 flux loss** is 7.50%, conditional on the reported photometric errors, the local baseline and its sampling assumptions. A single observation cannot trace the ingress, egress or repeatability.

The two full-quality halfway exposures belong to the same visit and share a baseline. Their W1−W2 colors differ from that visit's median by **−0.023 ± 0.033** and **+0.025 ± 0.033 mag**. The data do not establish a secondary eclipse or a color change. An eccentric secondary eclipse can occur away from halfway. An eclipsing binary with a 112.16-day orbit and alternating minima separated by 56.08 days would place both kinds of minima at integer cycles of the adopted photometric ephemeris. [Per-exposure calculations](eclipse_windows.csv) · [Paired colors](colors.csv)

## Timing and local photometry

The calculation uses BJD(TDB) 2458447.10503 + 56.0793594 × cycle, transforming archive UTC times to TDB and adding the projected Earth-to-barycenter light-travel time. WISE's low-Earth orbit contributes less than 0.03 seconds beyond the geocentric approximation. For early NEOWISE observations the analysis applies IRSA's 1.57-second timestamp correction. The observing visits are separated by gaps over 30 days. The separation between consecutive NEOWISE sampling blocks in these data is at least 149 days. [Timestamp conventions](https://irsa.ipac.caltech.edu/data/WISE/docs/release/NEOWISE/expsup/sec2_2.html)

For each band and tested exposure, the reference is the same-visit median outside ±2.61 hours of both predicted centers. Strict selection uses full frame quality, positive South Atlantic Anomaly separation, clean contamination and moon flags, and a single undecomposed source. NEOWISE also requires a positive frame score, A-grade band photometry, zero saturation and transient-pixel flags, and reduced profile-fit chi-square below 2. The relaxed selection changes only the frame-quality factor from 1 to positive. The same-visit reference reduces seasonal zero-point offsets, which are particularly relevant in W2. [NEOWISE quality and calibration caveats](https://irsa.ipac.caltech.edu/data/WISE/docs/release/NEOWISE/expsup/sec2_2.html)

Positive flux loss denotes a fainter source. Per-exposure uncertainty propagates the archive magnitude error and an estimated error of the local median, using the median absolute deviation scaled to a Gaussian standard deviation. These are formal errors. Correlated scan or calibration errors can enlarge them. For the primary W2 comparison, the scaled median absolute deviation is 0.0274 mag and the exposure's reported error is 0.0300 mag. The two full-quality halfway points are reported separately to preserve their shared observing conditions.

The nearest AllWISE catalog neighbor is **7.76 arcseconds** from the Gaia position. Its catalog flux is 1.81% of the target's in W1 and 3.10% in W2. The bands' nominal resolutions are 6.1 and 6.4 arcseconds. The eclipse-window rows have unit blend multiplicity in the NEOWISE fits, though that flag cannot rule out light from an unresolved companion or leakage from a nearby source. These data cannot distinguish a planet from a grazing stellar companion or an unresolved eclipsing system. [Nearby source measurements](neighbors.csv) · [WISE instrument resolution](https://arxiv.org/abs/1008.0031)

## Reproduction

The exposure table and neighboring-source table were obtained independently through IRSA TAP and Gator. Both returned the same 672 target exposures. The supplied exposure table allows all timing, baseline and color calculations to run offline with Python, NumPy, pandas and Astropy. To regenerate the inputs, `fetch.py` also requires `requests`. The 3-arcsecond exposure cone and the 60-arcsecond neighbor cone are the spatial scope of the search.

```sh
python analyze.py
python fetch.py
python analyze.py
```
