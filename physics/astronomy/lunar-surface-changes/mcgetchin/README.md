# A candidate secondary depression northwest of McGetchin crater

At **1.36151° N, 67.16426° E**, a several-metre feature at the end of a bright ejecta streak has acquired the lighting signature of a hollow. It lies **442 m from the center of McGetchin crater, at bearing 303°**. Low sunlight from opposite directions reverses the bright and dark sides. The change appears in different camera exposures. Local stereo matching also places the center below its surroundings at short matching scales. Ballistic excavation by McGetchin ejecta is one explanation. Ejecta deposited unevenly around shallow pre-existing relief could produce the same observations. The available pre-impact topography cannot distinguish these mechanisms.

[Before and after under matched lighting](sequence-NW.png) · [High Sun and reversed low Sun](albedo-and-reversal.png) · [Stereo profiles](stereo-profiles.png) · [Search field](field-locations.png) · [Positions on the published map](published-map.png)

## What changed, and when?

The high-Sun measurement compares the mean inside a 3 m radius with the median at radii 13–21 m in each image. The low-Sun measurement is the natural logarithm of the west/east brightness ratio in two 3 × 3 m apertures whose centers are 4 m apart. Both ratios are dimensionless.

| Observation at the NW center | Before | After |
|---|---:|---:|
| High-Sun center / surrounding terrain | 0.995, 9 Apr 2022 | 1.179, 28 Nov 2025 |
| West/east log ratio, east Sun | −0.053, 9 Dec 2010 | +0.707, 22 Jan 2026 |
| West/east log ratio, west Sun | +0.451, 22 Mar 2019 | −0.995, 30 Jul 2026 |
| Additional east-Sun view | −0.019, 20 Feb 2018 (49° incidence) | +1.145, 17 Jul 2026 (81° incidence) |

The site brightened between **9 April 2022 and 28 November 2025** in the available near-noon comparison. For the hollow, the last informative pre-impact low-Sun image examined is **22 March 2019**. A moderate-Sun image and the stereo sequence show the relief by **25 December 2025**. A November 2023 image footprint includes the site at 94.6° solar incidence, beyond the local horizontal horizon. The brightening and hollow have different observational brackets. The independently established **11 April–22 May 2024** formation interval applies to the primary crater. Association of the NW change with that impact rests on the position of the ejecta streak and the image sequence. [NASA event chronology](https://science.nasa.gov/solar-system/moon/nasas-moon-orbiter-spots-new-once-in-century-moon-crater/) · [Albedo measurements](albedo.csv) · [Lobe measurements](lobe-contrasts.csv) · [Earlier footprint metadata](pre-impact-footprints.csv)

The sharpest pre-impact frame in the footprint query, M1273794308RC (0.808 m native map resolution), shows broader irregular relief but no comparable east-lit central pair. A pre-existing pit 31 m away has the expected concave lighting reversal in both epochs, including a pre-impact west-Sun contrast of −2.31. The NW before/after polarity change survives all nine integer center displacements of up to 1 m in each direction. For east Sun the pre-impact range is −0.118 to −0.032 and the January 2026 range is +0.307 to +0.707. For west Sun the ranges are +0.207 to +0.673 and −1.131 to −0.144. [Old crater control](sequence-old_pit_control.png) · [Center-shift sensitivity](center-shift-sensitivity.csv)

## Depth and position

At a 7-pixel matching window, median central stereo height relative to an annulus of radii **4.4–7.15 m** is −0.37 m (east–west), −0.51 m (east–nadir), and −0.44 m (nadir–west). In each pair, every quadrant of the annulus has a higher median than the center. All pairs share exposures in the same December 2025 three-view sequence. The spread measures sensitivity to view combination. It is not a formal uncertainty interval. Five- to nine-pixel windows give −0.27 to −0.73 m across the three pairs. At fifteen pixels all three values change sign. The east–west profile is asymmetric. The western flank stands high, and the sampled floor is close to the broader locally detrended level. Ejecta buildup at the flanks could therefore account for the local low. The published 3 m terrain model gives −0.01 m at the same aperture, too small to resolve. An identifiable continuous rim and a measured rim-to-rim diameter are lacking. [Stereo apertures and window sensitivity](stereo-apertures.csv) · [Stereo map panels](stereo-maps.png) · [Camera geometry and primary metadata](stereo-geometry.json)

The center has zero-based sample/line **377.90, 25506.14** in M1540060927RC (30 July 2026), **487.70, 26064.46** in M1538900584RC (17 July 2026), and **280.71, 440.99** in the distributed 2018 GeoTIFF. These fractional coordinates identify an interpolated sample. Around NW the 2010/January east-Sun pair and 2019/July west-Sun pair each yield 72 accepted surrounding registration patches, with median integer displacement (0, 0) and median correlations 0.857 and 0.876. The 2018/December moderate-Sun pair yields 52 ties, median (0, 0), and 75th-percentile offset 1 m. These are local alignment tests. Absolute lunar coordinates inherit the archived projection and orbit uncertainties. [Source pixel addresses](image-coordinates.csv) · [Local registration measurements](local-registration.csv)

## Published geology and the northern site

Robinson et al. mapped the ejecta contour, pre-existing craters and newly deposited boulders. On a nominal overlay of their Figure 7, NW is **about 7 m from a detached contour**. The overlay uses the published center and scale. Its positional uncertainty relative to individual contour segments has not been measured. The nearest colored boulder symbol is roughly 60 m away. Neither their map nor the regional thermal study identifies a secondary crater at this exact position. The map shows surviving old craters larger than 12 m and obscured old craters larger than 6 m. A smaller old hollow at NW could therefore be absent from the published inventory. The published 22 m pre-impact Kaguya DEM also averages over this feature. The source map is a drawn raster. Distances from its boundaries and symbols are approximate. [Robinson et al., Fig. 7](https://pmc.ncbi.nlm.nih.gov/articles/PMC13580579/#F7) · [Powell et al., regional ejecta and thermal observations](https://pmc.ncbi.nlm.nih.gov/articles/PMC13580542/)

At **1.36154° N, 67.17864° E**, 250 m from the primary at bearing 15°, a second illumination reversal occurs on the northern ejecta tongue. The sampled trough lies approximately 12 m from the center of an already mapped old crater. Stereo gives a depressed center relative to the complete annulus, though one quadrant in the nadir–west pair lies below the center. Differential burial or remodeling of old crater terrain fits the observations. This site is classified separately as **remodeled terrain**. [Northern site sequence](sequence-NNE.png) · [Map comparison](published-map.png)

## Field selection and false positives

The search covered 994,688 one-square-metre grid cells at radii 160–585 m from the primary. The initial search subtracted near-noon albedo from moderate- and low-Sun images, measured directional shading against two pre-impact frames, and scanned seven Gaussian scales (1–11 m). It returned 156 scale extrema, or **85 spatially separated locations**, including 35 beyond 280 m. Scores were normalized by the median absolute deviation of residuals in the outer field. Opposite-Sun follow-up had geometric coverage at all 85 locations. Six reached an empirical follow-up score of 3, two reached 3.5, and none reached 4. NW scored 7.61 initially and 3.61 on follow-up, at the same grid cell.

A separate whole-field pass with the opposite-Sun score returned 116 spatially separated peaks above 3 and six above 4. Its northern-tongue peak was at (664, 359), one metre west of the sampled trough. Two high-ranked responses at (260, 1038) and (181, 956) occupy noisy dark portions of the July west-Sun detector. The corresponding 45 m before/after neighborhoods have log-brightness correlations −0.11 and −0.04 under the same west-side lighting, compared with +0.75 at NW. A geometrical footprint includes low-signal detector margins. These rankings do not measure formal false-alarm probabilities, crater abundance, or survey completeness. [All initial extrema](all-peaks.csv) · [Independent positions](distinct.csv) · [Cross-check of all 85](replication.csv) · [Opposite-Sun extrema](opposite-extrema.csv) · [Separated opposite-Sun peaks](opposite-distinct.csv)

## Reproduction

All scripts use the folder containing them as the results directory. Run commands there. The compact chips retain registered 65 × 65 source samples for each site and epoch on a common 1 m grid. Zenodo frames are calibrated I/F, PDS cutouts preserve calibrated signed-detector counts after invalid-code masking, and DTM values are metres above the lunar reference sphere. Ratios within an observation remove the multiplicative detector scale. All published products retain their original archives independently of this package.

```sh
python -m pip install -r requirements.txt
python chips.py
python site_figure.py
```

The first script checks 24 log-ratio measurements and three stereo contrasts directly from the compact arrays, then calculates the high-Sun brightness ratios. To rebuild the arrays and plots from the archived images, run the following in order. The default raw-data directory is `data`. The `MCGETCHIN_DATA` environment variable can point to another archive cache.

```sh
python fetch.py
python field.py
python search.py
python opposite.py
python relief.py
python triangulate.py
python coordinates.py
python figures.py
python chips.py --extract
python site_figure.py
python map_check.py
```

The reference run used Python 3.13, NumPy 2.4.2, SciPy 1.17.1, OpenCV 4.13.0, pandas 3.0.2, Pillow 12.1.0, Matplotlib 3.10.8, Requests 2.32.5 and threadpoolctl 3.6.0. A second run from the archived inputs reproduced the 30 registered cutouts, 12 stereo relief maps and eight figures pixel for pixel.

`fetch.py` verifies both archive MD5 checksums against the Zenodo record. `opposite.py` fetches PDS product headers and detector-row ranges, checks byte-range responses, and caches them. It uses the observation geometry in [extra-observations.json](extra-observations.json). A July west-Sun left frame produced insufficient registration support. Its right companion supplies the sites. All analysis is sequential by script with at most four OpenCV/BLAS threads in the field processing. Downloads use Requests with its default of no elapsed-time cutoff and no automatic connection retries. A network failure stops that command; completed cached products can be reused on a later run.

The grid is north up with x increasing east and y increasing south. Its origin is the northwest corner (−3,421,266 m, +41,646 m) of a 1,200 m equirectangular crop. Projection parameters are center meridian 180° E, standard parallel 1° N and radius 1,737,400 m. Common-grid (600,600) is the reference primary center. In the ranking tables `sigma` is the Gaussian scale in metres and `score` and `relief_z` are empirical normalized residuals. In the stereo tables `window` is the correlation width in grid pixels, `center_minus_annulus` and the four sector contrasts are metres, and `center_fb_error` is median forward/backward displacement mismatch in pixels. Figure panels are contrast-stretched independently.

The source products are LRO/LROC NAC observations from NASA/GSFC and the LROC team. The georeferenced NAC images, orthophotos and terrain model are distributed with Robinson et al. The map comparison adds location rings to crops of their CC BY 4.0 Figure 7. [Data record and download](https://doi.org/10.5281/zenodo.21481275) · [Research article](https://doi.org/10.1126/sciadv.aeh7812) · [LROC instrument team](https://www.lroc.im-ldi.com/images/1501) · [Map reuse terms](https://creativecommons.org/licenses/by/4.0/)
