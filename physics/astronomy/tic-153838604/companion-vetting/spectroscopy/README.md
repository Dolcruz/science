# Radial-velocity evidence for TIC 153838604

**Gaia DR3 measured a combined barycentric velocity of +75.61 ± 2.03 km/s for this star. The public measurements checked on 20 November 2026 do not determine the companion's mass.** The 22 Gaia observations span 888.14 days and 19 distinct visibility periods. Gaia combined the observations to obtain one velocity. No individually dated velocity for this star was recovered in the archives below. [Gaia source data model](https://gea.esac.esa.int/archive/documentation/GDR3/Gaia_archive/chap_datamodel/sec_dm_main_source_catalogue/ssec_dm_gaia_source.html) · [Archive query results](archive_snapshot.json)

## What the Gaia error measures

The source is Gaia DR3 4788303839668784896 at ICRS (68.07398832°, −47.60899384°), epoch J2016.0. Its RVS magnitude is 12.17365 and its processing flag is `rv_method_used = 2`. For this method Gaia aligns and combines the transit cross-correlation functions, then estimates the uncertainty from the curvature and height of their combined peak. Converting 2.03 km/s into a sample standard deviation by multiplying by a factor involving √22 would use the formula for a different processing method. The published robust velocity range, variability probability and renormalized goodness-of-fit are all null. Three transits were deblended. [Gaia's velocity processing and validation](https://arxiv.org/abs/2206.05902)

An unknown systemic velocity can shift the combined peak. Without the epoch velocities or a calibrated model for how an orbit, intrinsic line width, photon noise and sampling change the peak, the aggregate and its curvature do not yield a model-independent limit on the orbital semiamplitude. For scale, a circular, edge-on 56.07936-day orbit around a one-solar-mass primary would give primary-star semiamplitudes of **0.053, 0.685 and 4.04 km/s** for companions of 1, 13 and 80 Jupiter masses, respectively. These values are illustrative predictions. The TIC stellar mass is 1.00 ± 0.12 solar masses. Unresolved blends or an orbital period twice the photometric recurrence would change the interpretation. [ExoFOP target parameters](https://exofop.ipac.caltech.edu/tess/target.php?id=153838604)

The DR3 flags indicate no published epoch RV series and no published mean RVS spectrum. DR2 reports zero RV transits. Queries of the DR3 and Focused Product Release variable-star RV epoch tables each returned zero rows. A low-resolution mean BP/RP spectrum is available, assembled from 29 blue and 38 red transits. These are not individually dated Doppler measurements. [Gaia DR3 archive](https://gea.esac.esa.int/archive/) · [Focused Product Release description](https://gaia.aip.de/metadata/gaiafpr/)

## Ground-based spectroscopy

Stellar catalog searches used a 60-arcsecond cone or a rectangular prefilter containing that cone. Ground-based observation-log searches used the sky position, with a 5-arcminute pointing radius or enclosing box. Gaia's measured proper motion is 51 milliarcseconds per year, well within these apertures over the observing dates. The full request URLs and parsed results are in the accompanying snapshot.

| Archive | Search and outcome |
|---|---|
| GALAH | DR3 and DR4 per-spectrum catalogs returned zero rows in the position box. The DR4 per-spectrum table also returned zero for the exact Gaia identifier. [GALAH DR4 release](https://www.galah-survey.org/dr4/the_catalogues/) |
| RAVE and Gaia–ESO | RAVE DR6 observation table returned zero rows within 60 arcseconds. The Gaia–ESO DR5.1 catalog and the 2021 velocity catalog each returned zero in the position box. [RAVE observation table](https://doi.org/10.17876/rave/dr.6/003) · [ESO Gaia–ESO catalog](https://www.eso.org/qi/catalog/show/411) |
| SDSS | APOGEE DR17 star and visit tables each returned zero in the position box. The SDSS-V DR20 Valis cone query returned an empty list. [SDSS DR20 data access](https://www.sdss.org/dr20/data_access/zora_and_valis/) |
| ESO | Zero raw science target positions and zero raw telescope pointings fall in the box. Zero reduced ObsCore product centers fall within 5 arcminutes. The reduced footprints covering the target comprise 10 VIRCAM images and 15 measurement products. These searches include the ESO holdings for HARPS, FEROS and ESPRESSO. [ESO archive access and coverage](https://www.eso.org/cms/eso-data/programmatic-access.html) |
| ExoFOP and LCO/NRES | ExoFOP's spectroscopy and attached-file arrays are empty. The LCO footprint query returned 36 frames from imaging detectors, comprising calibration and trailed-image records. Searches for public spectra by TIC, 2MASS and UCAC identifiers each returned zero frames. LCO result counts were taken from the pages themselves. [ExoFOP](https://exofop.ipac.caltech.edu/tess/target.php?id=153838604) · [LCO archive API](https://developers.lco.global/) |
| NOIRLab | The position query returned 257 Legacy Survey DECam/WISE imaging and derived products. A CHIRON-specific query returned zero records in the pointing box. [NOIRLab archive](https://astroarchive.noirlab.edu/) · [CHIRON archival coverage](https://www.astro.gsu.edu/~thenry/SMARTS/CHIRON_FAQ.pdf) |
| Gemini and cross-archive index | Coverage in the direct Gemini archive is unknown. The public Spectra Pointer cross-archive index returned zero records within 1 arcminute, including unmatched records. Its coverage is incomplete. [Gemini archive API](https://archive.gemini.edu/help/api.html) · [Spectra Pointer positional query](https://astro.gsu.edu/~way/spectra_pointer/?ra=68.07398832&dec=-47.60899384&radius=1&mode=radius&search_unmatched=1) |

These results describe the queried public metadata. Pointing errors, unindexed spectra, private observations and unidentified targets remain possible.

## Gaia DR4

The public ESA TAP service listed no DR4 schema on 20 November 2026. Gaia scheduled DR4 for **2 December 2026**. The announced release includes individual single-lined and double-lined transit products, `rvs_epoch_parameters_single` and `rvs_epoch_parameters_double`, through DataLink. The documented cross-identification route is `dr3_neighbourhood`, because source identifiers can change between releases. Inclusion, precision and orbital-phase coverage for TIC 153838604 await the release. [Gaia DR4 schedule](https://gaia.aip.de/cms/data/catalogues/) · [ESA DR4 product map](https://www.cosmos.esa.int/web/gaia/dr4)

## Reproduction

`check_archives.py` requires Python and `requests`. It performs read-only public archive queries and writes JSON to standard output. It follows all LCO cursor pages. LCO documents 1,000 anonymous requests per 24 hours and a maximum of 1,000 records per page. The NOIRLab advanced search uses its server default of 1,000 rows per page, and the CHIRON query returned zero. Neither archive limit truncated these results.

```sh
python check_archives.py > new_snapshot.json
```
