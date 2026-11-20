# KELT-South observations of TIC 153838604

KELT recorded only one night in each of the two predicted eclipse windows. Both nights are consistent with zero depth and with an eclipse as deep as the approximately 1.57% TESS signal. This archive supplies no independent detection of the signal or a useful discriminator between the planetary and stellar interpretations.

## Data and phase coverage

The NASA Exoplanet Archive associates east source 043914 and west source 038023 in field S20. The archive position is 6.99 arcseconds from the Gaia target, within a 23-arcsecond KELT pixel. The photometry measures an aperture with possible contaminating light. The east and west instruments in the table refer to two pier orientations of the same telescope. The raw and trend-filtered (TFA) files share exposures. Across the two pier orientations, the archive contains 4,243 raw exposures on 485 nights and 4,160 TFA exposures on 484 nights, from February 2010 through April 2013. The magnitudes in the files are instrumental. [KELT archive and survey description](https://exoplanetarchive.ipac.caltech.edu/docs/KELT.html) · [Data definitions](https://exoplanetarchive.ipac.caltech.edu/docs/API_kelt_columns.html)

The fixed ephemeris is BJD 2458447.10503234 + 56.07935938 × E. Each 2.61-hour box extends 1.305 hours either side of its center. Phase zero is sampled by eight eastern exposures on BJD integer day 2455867. Phase 0.5 is sampled on day 2455895 by nine western exposures and one eastern exposure at the leading edge. These occur 46 cycles and 45.5 cycles, respectively, before the TESS reference event. The folder includes the four full light curves and their source URLs. [NASA source-specific archive manifest](https://exoplanetarchive.ipac.caltech.edu/cgi-bin/IERDownload/nph-IERDownload?id=KELT_S20_lc_043914_V01_east&dataset=KELT&inventory_mode=id_single&idtype=source&resultmode=stream)

## Night-level photometry

The measured contrast is the mean magnitude inside the box minus the mean outside on the same night and pier. Positive values mean fading. For each other night with sufficient visits on that pier, the calculation reproduces the observed sequence of inside/outside labels relative to the eastern sequence's end or the western sequence's start at the meridian. Each control night contributes once. The control-corrected contrast subtracts the median control difference. The empirical span subtracts the 97.5th and 2.5th control percentiles from the observation. These spans describe repeat-night scatter. Their tails have limited precision given the small reference samples.

| TFA phase and pier | In / out | Control nights | Observed difference | Control-corrected difference | Empirical span |
|---|---:|---:|---:|---:|---:|
| 0, east | 8 / 4 | 22 | −9.2 mmag | +6.2 mmag | −96.8 to +53.1 mmag |
| 0.5, west | 9 / 5 | 27 | −7.4 mmag | −15.1 mmag | −52.3 to +33.5 mmag |
| 0.5, east | 1 / 12 | 9 | −2.0 mmag | +37.6 mmag | −24.8 to +112.1 mmag |

A TESS-like depth corresponds to a 17.2 mmag full-box drop before KELT-specific dilution, bandpass differences or detrending. In the raw data the control-corrected differences for the better-sampled tests are +2.0 mmag at phase zero and −8.7 mmag at phase 0.5. This analysis assumes an unchanged ephemeris and uses a box extending across ingress and egress. It includes sensitivity runs with both centers shifted by ±10 minutes. The sparse windows cannot test a secondary at arbitrary orbital phase.

Run `python analyze.py` with Python, NumPy and pandas to regenerate `kelt-result.json` and `night-controls.csv` from the four archive files.
