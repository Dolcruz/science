# ASAS-SN measurements at the TESS eclipse times

Sky Patrol V2 identifies ASAS-SN source 420907781706 with Gaia DR3 source 4788303839668784896. Of 1,820 measurements, 1,616 have survey quality G and positive flux. The four measurements inside the 2.5-hour primary windows were taken on **23 December 2017, 4 August 2018, 30 August 2021 and 25 October 2021**. All are from *g*-band cameras. At the opposite phase three accepted measurements fall in the 2.5-hour windows. [Sky Patrol V2](https://arxiv.org/abs/2304.03791) · [Survey reduction and photometry](https://asas-sn.github.io/skypatrol/additional.html) · [Camera filters](https://asas-sn.osu.edu/)

The eclipse predictions use the four TESS midpoints alone. A crossmatch against the earlier ASAS-SN V-band archive identifies 338 V2 camera exposures with legacy timestamps within 15 minutes. The median absolute timing difference falls from 119 seconds to 8 seconds after the expected heliocentric correction is applied to V2. This supports treating V2 Julian dates as observer dates. The main analysis converts them from UTC to barycentric TDB at the star, ignoring subsecond differences between the observatory and geocentre. Alternative timestamp conventions give similar primary depths. The legacy V time series contains zero primary measurements in the 2.5-hour window. [Legacy light curve](https://asas-sn.osu.edu/photometry/e58fabb7-bc30-58ce-b45f-424097ef0a3f) · [Timing sensitivity](depths.csv)

Each measurement is compared to the median of separate nights from the same camera within 30 days on either side, excluding the event night and both predicted eclipse windows. We also applied 14- and 60-day windows. The fitted quantity is the peak depth of a triangle with 2.5-hour total width at the known phase. The published survey errors can be smaller than the night-to-night scatter. The fit weights use the measured scatter of the control nights.

Two disjoint sets of comparison stars were selected to lie within 0.6 Gaia magnitudes and 0.35 magnitudes in BP−RP of the target. The inner field contains ten stars between 1 and 15 arcminutes, the outer field 39 stars between 15 and 30 arcminutes. Each star is normalized by its own camera-specific local median. The median of the reference values in each image corrects its target flux. Three reference stars are required in an image to estimate this median. The inner field supplies just two on one of the four primary images. The outer field supplies 20 to 39 references on all four.

| Calibration | Primary nights | Fitted *g* depth | Nominal 95% interval | Achromatic prediction from TESS |
|---|---:|---:|---:|---:|
| Target only | 4 | 2.82% | 1.15–4.28% | 1.56–1.57% |
| Inner field | 3 | 2.59% | −0.93–4.38% | 1.50% |
| Outer field | 4 | 2.82% | 1.09–4.37% | 1.51% |

The predicted depths apply exactly the ground-survey estimator to each TESS model sampled at the actual ASAS-SN times. Each ASAS-SN point usually combines three 90-second images. The nominal intervals invert the distribution of independent matched-night residuals while keeping estimated weights fixed. At these small sample sizes the uncertainty in those weights matters. [Estimator predictions](achromatic-predictions.csv) · [Outer-field data](outer-field/differential-0-events.csv)

An additional test reassigns the putative eclipse night among each measured night and its controls, recomputing baseline and noise weight under every assignment. Using the outer reference field, 50 of 19,551 assignments give at least the observed dimming under a zero-loss model. For the two TESS-shaped signals the one-sided excess-dimming fractions are 0.0773 and 0.0776. The ten-star field with three events gives 0.121 against zero and 0.196 against either TESS signal. All tests assume exchangeable nights within each matched set, and the three reductions share data. The measurements support an eclipse at the TESS times. The distinction between the two mass models and the apparent colour difference are both unresolved. [All finite-control tests](permutation.csv)

## Reproduction

With the sibling TESS results in place, use Python, NumPy, pandas, PyArrow, requests, Astropy and batman-package. The scripts use the supplied Parquet tables. The first two can retrieve those tables through the survey's public API if absent.

```
python analyze.py
python comparison_stars.py
python compare_bands.py
python night_permutation.py
```
