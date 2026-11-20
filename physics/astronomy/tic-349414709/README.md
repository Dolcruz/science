# The 2.709-day eclipse published for TIC 349414705 comes from TIC 349414709

IJspeert et al. (2024) list a 2.71-day eclipsing-binary signal under TIC 349414705. The eclipse is on **TIC 349414709** (Gaia DR3 5715476503089307520), about 15 arcseconds to the southeast. Ground photometry that resolves the two stars shows TIC 349414709 losing **11.7 ± 1.2% (r′) and 11.4 ± 0.8% (i′)** of its light in eclipse, while TIC 349414705 changes by 0.2 ± 0.7% and 0.5 ± 0.8%, consistent with no eclipse. [IJspeert et al. 2024](https://doi.org/10.1051/0004-6361/202450507) · [Published catalogue](https://cdsarc.cds.unistra.fr/viz-bin/cat/J/A+A/691/A242)

**What this does not show.**

- **Ground timing:** The ground eclipses of 2011 to 2013 arrive **39 minutes earlier** (1σ range 37 to 43 minutes) than the TESS-only ephemeris predicts, although the ephemeris uncertainty at those epochs is only 2 to 7 minutes. The cause is open: an unrecognised timestamp convention in the archive photometry, or real eclipse-timing variations. The 2017 to 2018 data are too sparse to tell. The source attribution does not depend on this.
- **Prior flag:** The NASA SPOC pipeline already reports the eclipse 15.15 ± 2.50″ from the nominal target. What this entry adds is the resolved ground confirmation and the identification of the host.
- **Mass and radius:** The companion mass and radius are unknown.
- **Selection:** The field was selected retrospectively from displaced TESS eclipse signals. It says nothing about how often such misattributions occur.

[Illustrated report (PDF)](report.pdf) · [Editable LaTeX](report.tex) · [Catalog and prior-publication comparison](catalog-comparison.md) · [Second review: timing and centred depths](review/centred_window.py)

![TESS light curves, Bochum photometry, and TESS difference-image positions](eclipse-source.png)

## Which star is eclipsed

| Ground source (Bochum Galactic Disk Survey) | r′ loss, centred | i′ loss, centred | r′ / i′ loss at the TESS-predicted centre |
|---|---:|---:|---:|
| TIC 349414709 | 11.68 ± 1.22% | 11.36 ± 0.78% | 10.62% / 10.67% |
| TIC 349414705 (published target) | 0.18 ± 0.68% | 0.52 ± 0.80% | 0.16% / 0.69% |
| TIC 349414726 (field control) | 0.22 ± 1.23% | 0.54 ± 1.89% | −0.18% / 1.64% |

"Centred" uses the eclipse window shifted by the measured −39 minutes; uncertainties are bootstrap standard deviations of the median contrast. The right-hand column uses the window at the TESS-predicted time, as in the original study. There, three to four of the in-window points fall outside the eclipse, which lowers the median. [Centred depths](review/centred-depths.csv)

**Within the close pair,** the brighter star is the host. Gaia resolves a second source 0.918″ from TIC 349414709, 3.31 magnitudes fainter in G, so it supplies about 4.5% of the light. A star that contributes 4.5% of the G-band light cannot produce an 11.7% dip in r′, a band that lies inside the G passband. The two depths are also equal within errors in r′ and i′. In addition, the faint source has parallax 0.40 ± 0.13 mas against 2.23 ± 0.06 mas for the bright star. It is a background star, not a physical companion. The bright star's Gaia RUWE of 5.12 fits an unresolved binary.

**TESS.** Seven sector 108 primary eclipses give a mean difference-image centroid at ICRS (114.518881°, −20.393012°). At the observing epoch this is 1.93″ from TIC 349414709 and 14.76″ from TIC 349414705; a TESS pixel spans about 21″. The NASA SPOC pipeline independently reports a 15.15 ± 2.50″ offset from the nominal target. The deeper eclipses in the older apertures centred on TIC 349414709 (10.0 to 11.8%) compared with the sector 108 aperture on the brighter nominal target (2.76%) are expected whichever star hosts the eclipse, because the flux ratio differs between apertures. They are not localisation evidence on their own. [Sector 108 pixel product and other archive links](source-products.csv)

## Ephemeris

From 40 primary eclipses in TESS sectors 7, 34, 61, 88 and 108:
`BJD(TDB) = 2461293.6916 (± 0.0019) + 2.7091724 (± 0.0000032) × cycle`. The timing residuals have RMS 10.3 minutes. The sector 108 timings come from an aperture centred on the brighter neighbour, which dilutes the eclipse; without them the RMS is 2.7 minutes and the period 2.7091722 ± 0.0000011 days. A weaker trough near phase 0.505 appears in sectors 34, 61, 88 and 108, which supports the 2.709-day period over the doubled one and indicates a slightly eccentric orbit. [MIT Quick-Look Pipeline at MAST](https://archive.stsci.edu/hlsp/qlp) · [NASA TESS sector 108 threshold-crossing events](https://archive.stsci.edu/missions/tess/catalogs/tce/tess2026250113507-s0108-s0108_dvr-tcestats.csv)

## Prior identification

IJspeert et al. list TIC 349414705 with period 2.7084875683 days and reference primary BTJD 2232.014957084 (and a doubled period of 5.4170243594 days). Their catalogue targets O-, B-, A- and F-type stars and lists this entry with Teff 8033 K. That temperature belongs to the bright nominal target, which Gaia, VSX and SIMBAD list as a δ Scuti or γ Doradus pulsator. The eclipse is on a G-type star at about 450 pc (TICv8: 5701 ± 138 K, 0.92 solar radii). No catalogue checked on 20 November 2026 lists TIC 349414709 or its Gaia source as variable: Gaia DR3 eclipsing binaries and variability summary, VSX (October 2026 edition), Prša et al. 2022, Kostov et al. 2025 (only the neighbour TIC 349414726, unvetted), ASAS-SN, ZTF, ATLAS, Gavras et al. 2023, the Bochum variability catalogue and SIMBAD. ExoFOP lists no TOI or CTOI for either star. A VSX entry added after October 2026 cannot be excluded. [Catalog comparison](catalog-comparison.md)

## Reproduce the measurements

Python with NumPy, pandas, SciPy, Matplotlib and Astropy is sufficient. Run from this directory:

```sh
python timing/verify.py
python measure.py
python review/centred_window.py
```

`measure.py` writes the figure, four main numerical tables and a timing sensitivity table, using the eclipse window at the TESS-predicted time. `review/centred_window.py` measures the ground eclipse centre per era and recomputes the depths in a re-centred window. All 373 distinct Bochum time stamps match same-filter observatory frames within 0.472 seconds. The reduction converts the recorded observatory UTC times to barycentric TDB; the VOTable labels the same values barycentric TCB. [Frame matches and timing sensitivity](timing/README.md)

To rebuild the compact inputs from all twelve source products:

```sh
python rebuild.py archive-cache
python measure.py
```

NASA's TESS mission provided the spacecraft measurements, SPOC the sector 108 pipeline products, MIT the Quick-Look Pipeline light curves, and STScI distributed the data through MAST. Ground data are from the Bochum Galactic Disk Survey via GAVO ([Blex et al. 2026](https://doi.org/10.1002/asna.70087)). The stellar context uses the TESS Input Catalog, 2MASS, and ESA's Gaia mission. Prior publications were checked through CDS VizieR.

## Authorship and review

OpenAI Codex agents carried out the archival search, measurements, figures and the first version of this text. The original observations and catalogue entries are the work of the survey and network teams credited above.

- **First review** (OpenAI Codex, GPT-6 family): rebuilt all 1,119 ground measurements, the TESS light curves and the difference images from the 12 archive products of [the study commit](https://github.com/Dolcruz/science/commit/0a37850d631ce6a5e03d2050ee94da428c1178c9), and resolved the conflicting archive time labels. [Timing evidence](timing/README.md)
- **Second review** (Claude Code, 21 November 2026, study commit 12e5118):
  - reran `measure.py`, `timing/verify.py` and `rebuild.py` against the archives, with matching outputs;
  - checked the IJspeert catalogue row, the SPOC sector 108 offset, the Gaia DR3 parameters of both close sources and the variability catalogues;
  - found the −39 minute ground timing offset and corrected the depths, the ephemeris uncertainty and the host argument in this README and the report. `review/centred_window.py` reproduces the new numbers.
