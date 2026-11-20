# A July 2026 lake drainage on the western Greenland Ice Sheet

A supraglacial lake near **67.12718° N, 48.53845° W** expanded from **1.676 km² on 16 July to 5.819 km² on 20 July 2026**. By 23 July, only **0.442 km²** of water remained exposed in the same basin window. Sentinel-2 measured a loss of **5.377 km², or 92.4%**, in 72 hours 10 minutes. Landsat independently recorded the change. Cloud-penetrating radar shows that a broad, water-like surface persisted into the morning of 22 July.

The basin was mapped in 2018 and 2019. The July 2026 result measures exposed surface area. Water volume, drainage route and the duration of active flow remain open.

[Illustrated report (PDF)](report.pdf) · [Editable LaTeX](report.tex) · [Weather station record](weather/README.md) · [Separate Alaska screen and its null result](alaska-screen/README.md)

[Sentinel-2 sequence](lake-sequence.png) · [Landsat sequence and cloud masks](landsat-sequence.png) · [Radar sequence](radar-sequence.png) · [Chronology](chronology.png) · [Regional controls](comparison-pools.png) · [Positions in GeoJSON](sites.geojson)

## Chronology

| UTC, July 2026 | Observation |
|---|---|
| 15, 14:42 and 14:53 | Landsat 8 and Sentinel-2B measured 1.302 and 1.288 km² of exposed water. |
| 16, 15:13 | Sentinel-2C measured 1.676 km². |
| 20, 14:54 | Sentinel-2C measured 5.819 km² across the filled basin. |
| 21, 14:55 | Landsat 9 measured **at least 4.465 km²**. The USGS cloud and shadow mask left 72.4% of the basin window usable. The remaining clear pixels show a continuous dark-blue lake. |
| 22, 09:36 | Sentinel-1C still recorded a broad dark radar return across the 20 July optical footprint. Cloud obscured both optical products examined on this date. |
| 23, 14:43 and 15:04 | Cloud-free Landsat 9 and Sentinel-2C measured **0.413 and 0.442 km²**. Textured ice and several small remnant pools occupy the former lake. |
| 23, 20:47 | The broad radar-dark patch had disappeared. The interior now scattered radar much like adjacent ice. |
| 25 and 29 | Sentinel-2A measured 0.535 km² on 25 July. Landsat 8 measured 0.185 km² on 29 July. |

The three-day Sentinel-2 comparison measures the full optical area loss. A second, narrower bracket runs from the persistent radar signature at **09:35:47 UTC on 22 July** to the first clear, largely empty Landsat view at **14:42:35 UTC on 23 July**, or **29 hours 7 minutes**. This brackets the transition from widespread water-like backscatter to a mostly exposed basin. The timing of individual portions of the 5.377 km² loss is unresolved. [Optical measures](optical.csv) · [Radar measures](radar.csv)

## Physical interpretation

Rapid drainage best explains the loss of blue water, reappearance of surface texture, persistence of small pools and transition in radar return. A separate pool about 3.5 km southeast at **67.09970° N, 48.50047° W** retained exposed water across 91.6% of its sampled interior on 23 July. The same circle was entirely water-covered on 16 and 20 July. All six objectively selected test locations are shown, including neighboring pools that also shrank. Above-freezing air at the regional KAN_M weather station during the final transition further disfavors regional freeze-over. Site-specific surface temperature, water depth, vertical drainage, downstream discharge and the route taken by the water were not measured. These observations cannot distinguish an open surface outlet, drainage through fractures or a combination. [Pool controls](controls.csv) · [PROMICE station comparison](weather/README.md)

## Optical and radar measurements

The basin was selected from a **40 × 24 km** screening field on Sentinel-2 tile 22WEV. The screen used 20 dates from the July–August search interval, choosing one scene per date with the least tile-level cloud below 35%. At 80 m it flagged connected water patches of 25–1,200 pixels whose apparent water fraction fell to 20% or less within eight days with over 90% usable later pixels. The largest flagged component contained 1,021 pixels. It reached the eastern edge of the search field and included connected channels. The 10 m analysis uses a complete, fixed basin window on neighboring tile 22WFV. The initial screen is reproducible with `python screen.py`. Its detections are candidates for follow-up. [Screening images](screen-scenes.json) · [Regional candidate pairs](regional-screen.csv)

The fixed 4.0 × 3.2 km basin window spans eastings 604,400–608,400 m and northings 7,446,400–7,449,600 m in WGS 84 / UTM zone 22N. It encloses the main lake and its immediate margins. The wider field contains other pools connected by narrow channels. The reported position is the centroid of 20 July classified water within the window. It is distinct from the centroid of the larger connected drainage network.

Sentinel-2 Level-2A surface reflectance is sampled at 10 m. Landsat Collection 2 Level-2 surface reflectance is sampled at 30 m. Water is selected by the ice-specific blue–red normalized difference, **(blue − red)/(blue + red + 0.0001) > 0.25**, with the small denominator offset expressed in reflectance units. The analysis applies each product's reflectance scale and offset. Sentinel-2 scene classes 0, 3, 8, 9 and 10 and Landsat QA_PIXEL bits 0–4 exclude missing pixels, cloud, cirrus and shadow. Ice/snow classes remain eligible for the spectral test. All three key Sentinel-2C basin windows and the 23 July Landsat window pass the mask completely.

| Index threshold | 20 July (km²) | 23 July (km²) | Area loss |
|---:|---:|---:|---:|
| 0.20 | 6.648 | 0.800 | 88.0% |
| 0.25 | 5.819 | 0.442 | 92.4% |
| 0.30 | 5.298 | 0.292 | 94.5% |

This range measures sensitivity to the classification threshold. Shallow margins, floating ice, slush, residual shadows and mixed shoreline pixels affect the estimated area. The clear 23 July cross-sensor difference is 0.029 km². Both images use optical reflectance and share some sources of error. [Dual-satellite lake-mapping methodology](https://tc.copernicus.org/articles/12/3045/2018/)

Sentinel-1 terrain-corrected HH backscatter provides a physically different contrast. The analysis averages gamma-zero power over 100 m squares and expresses each value in dB relative to the median of fixed nearby ice on the same pass. The fixed footprint includes 5.638 km² of 20 m cells whose four 10 m subpixels were at least 75% water on 20 July. Reference ice is at least 30 ten-metre four-neighbor dilation steps from the peak-date water mask. At a −4.5 dB threshold, **65.2%** of the footprint was radar-dark on 20 July, **68.7%** on 22 July and **2.0%** on 23 July. The fraction of reference ice passing that threshold was below 0.1% in all three images. At thresholds −3 to −6 dB the 22 July range was 65.6–72.6%, compared with 0.7–7.0% on 23 July. On repeated relative orbit 156, the −4.5 dB fraction was 1.0% on 16 July, 68.7% on 22 July and 1.4% on 28 July. Radar darkness depends on roughness, incidence angle, surface wetness and wind. The radar classes describe surface state and cannot be converted directly to optical water area. A 23 July adjacent radar slice has zero usable coverage and is explicitly flagged in the table.

The 120 m comparison disks were selected on **20 July alone**. Each is centered at the largest interior distance from the edge of a contiguous dark-water area with index above 0.35, following a 5 × 5 pixel opening. Components must cover at least 0.18 km² and contain the disk. Selection includes the main lake itself. All six disks had 100% water in the peak image. One remained above 90% on 23 July, three retained between 20% and 61%, and two were below 10%. [All disk coordinates, cloud masks and dates](controls.csv)

## Relationship to earlier observations

This basin held water in earlier melt seasons. In the 2018–2019 Russell–Leverett archive, the 20 June 2019 lake polygons cover 1.635 km² of the measurement rectangle, with **1.598 km² overlapping the 2026 water footprint**. The 13 July 2018 inventory gives 0.539 km² in the rectangle. An independent pan-Greenland 2019 inventory overlaps the 2026 footprint by 0.974 km². Archive definitions and sampling differ. These snapshots establish a recurring basin without setting a historical maximum. [Glen, Russell–Leverett archive](https://doi.org/10.5281/zenodo.16577959) · [Dunmire et al., Greenland-wide lake inventory](https://doi.org/10.5281/zenodo.4813833) · [Spatial comparisons](historical.csv)

The event-specific contribution is the measured July 2026 filling and drainage in this known basin. Searches through 20 November 2026 covered the coordinates, the Kangerlussuaq and Russell–Leverett area, and the July dates. The two historical archives and the published regional and Greenland-wide work examined do not report this episode. A published July drainage at Sermeq Kujalleq occurred farther north in **2022**. Unindexed observations and unpublished monitoring could exist. [Greenland-wide lake dynamics, 2017–2022](https://www.sciencedirect.com/science/article/pii/S0034425725003001) · [Sermeq Kujalleq event](https://www.nature.com/articles/s41561-025-01858-2)

## Data and reproduction

The archive includes pixel cutouts for three Sentinel-2 dates, two Landsat dates and three valid Sentinel-1 passes used for the principal comparisons. Sentinel-2 and Landsat arrays in the compact archive retain their integer science values and QA flags inside the fixed window, flattened in row-major order. The Sentinel-2 cutout is 320 × 400 cells. Radar arrays and comparison masks are on the wider 390 × 660 grid. Fractional area refers to nominal projected square metres. [Source identifiers, exact times, STAC metadata and unsigned archive URLs](observations.json)

```sh
python -m pip install -r requirements.txt
python verify.py
```

The offline check recomputes 24 threshold-specific optical areas and radar fractions directly from the included cutouts. To reproduce the full dated tables, figures and comparisons to historical polygons, run the following in order.

```sh
python fetch.py
python measure.py
python figures.py
python past_lakes.py
python verify.py
```

Source windows are cached under `data`. The `GREENLAND_CACHE` environment variable can specify another cache location. Downloads run sequentially, with no application time cutoff. For Microsoft-hosted files, the downloader follows the archive's HTTP 429 `Retry-After` interval and reuses its public access token until expiry. Other download failures stop the command. The two historical ZIPs are verified against their published checksums. A separate retrieval for one product from each satellite reproduced the analysis arrays exactly.

Sentinel-2 data are from Copernicus, distributed as cloud-optimized GeoTIFFs via Earth Search. Landsat data are from USGS Collection 2. Sentinel-1 HH data are from the Planetary Computer radiometrically terrain-corrected GRD collection. RGB panels use the same stretch within each instrument. [Earth Search](https://earth-search.aws.element84.com/v1/collections/sentinel-2-l2a) · [USGS Landsat Collection 2](https://www.usgs.gov/landsat-missions/landsat-collection-2) · [Sentinel-1 RTC collection](https://planetarycomputer.microsoft.com/dataset/sentinel-1-rtc)

## Study design and authorship

The basin was selected retrospectively from a regional screen. Agreement between sensors, comparison pools, and the threshold sensitivity constrain the interpretation. The separate Alaska summer screen supplies additional search context. Contains modified Copernicus Sentinel data (2023–2026). Landsat data are courtesy of the U.S. Geological Survey. KAN_M observations are an extract of the How et al. PROMICE/GC-Net data, distributed under CC BY 4.0. Third-party data retain their original terms. [Copernicus data access](https://dataspace.copernicus.eu/terms-and-conditions) · [PROMICE/GC-Net data DOI](https://doi.org/10.22008/FK2/IW73UU) · [PROMICE/GC-Net dataset description](https://pub.geus.dk/en/publications/promice-gc-net-automatic-weather-station-data/)

OpenAI Codex agents carried out the archival search, measurements, figures and interpretation. The original observations and catalog entries are the work of the survey and network teams credited above. Build the report in this directory with `pdflatex report.tex`.
