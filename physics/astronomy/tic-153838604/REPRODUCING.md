# Reproducing the TIC 153838604 analysis

Four TESS eclipses in sectors 5, 32, 97 and 98 give a recurrence interval of 56.0793594 days across 2018–2025. Two 2025 events distinguish the surviving 13-cycle alias of the original 729-day event separation. Both a giant planet and a faint eclipsing star fit the available photometry. [Four-event analysis](duotransit/README.md) · [Companion models and follow-up evidence](companion-vetting/REPORT.md) · [Original duotransit catalog](https://doi.org/10.1093/mnras/stad3783)

## Reproduce the measurements

These commands use Python 3.13.9 and the package versions in `requirements.txt`. Run them from this directory. The four sector light curves are included. The programs write the regenerated figure and tables to the current analysis directory.

```sh
python -m pip install -r requirements.txt
cd duotransit
python measure.py
python timing.py
python submultiples.py
cd ../companion-vetting
python eclipse_models.py
```

The ephemeris, model curves, parity fits, infrared analysis, ground-based light curves and Gaia field comparisons can all be reconstructed from the included data. The two full TESSCut pixel cubes, the sector-30 footprint product and the independent SPOC light curves are retrieved on demand. The archive URLs and FITS checksums accompany the relevant measurements.

| Evidence | Inputs and analyses |
|---|---|
| TESS timing and period aliases | Four original [QLP](https://archive.stsci.edu/hlsp/qlp) FITS products, measured midpoints, noise injections and submultiple tests. [Timing analysis](duotransit/README.md) |
| Pixel localization | Two measured difference arrays with control maps, a Gaia field table and a script that retrieves the original TESSCut products. [Pixel measurements](duotransit/pixels/README.md) |
| Eclipse geometry and secondary limits | Two physical models, six QLP sector light curves across the two data directories, empirical injection measurements and phase-sensitive limits. [Companion models](companion-vetting/REPORT.md) · [TESS photometry](companion-vetting/photometry/README.md) |
| Ground-based optical photometry | ASAS-SN target and reference measurements and KELT-South raw and detrended east/west light curves. [ASAS-SN](companion-vetting/ground-asassn/README.md) · [KELT](companion-vetting/ground-kelt/README.md) |
| Infrared photometry | WISE and NEOWISE single exposures, neighboring source photometry and eclipse-window comparisons. [Infrared measurements](companion-vetting/infrared/README.md) |
| Stellar luminosity and contamination | Gaia target and comparison samples, two VISTA cutouts, 2MASS, AllWISE, ExoFOP inventory and search tables. [Field analysis](companion-vetting/blends/README.md) · [Archive queries](companion-vetting/blends/queries.md) |
| Spectroscopy | Dated radial-velocity archive snapshot, query code and coverage descriptions. [Archive inventory](companion-vetting/spectroscopy/README.md) |

The [ExoFOP target page](https://exofop.ipac.caltech.edu/tess/target.php?id=153838604) provides the live public catalog record. The package preserves the identifiers, candidate entry and observing inventories in machine-readable form. Direct Gemini coverage is undetermined. Original survey credits and product identifiers are given in the component reports and FITS headers.

## Build the research note

From the result directory, run the following with pdfLaTeX. The three vector figures are included, so building the paper does not require Python or an archive query.

```sh
cd paper
pdflatex -interaction=nonstopmode -halt-on-error tic-153838604.tex
pdflatex -interaction=nonstopmode -halt-on-error tic-153838604.tex
```

To regenerate the figures from the measurements, run `python figures.py ..` from `paper/` with the packages in the [Python requirements](requirements.txt). [Data sources and acknowledgments](DATA-SOURCES.md)
