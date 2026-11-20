# Summer lake changes in Alaska

Five Sentinel-2 tiles were screened across the summers of 2023–2026. The sample contains 60 scenes from 14 July through 27 August, with up to three dates per tile and summer. Dates were chosen for cloud, snow and valid coverage and separated by at least five days. The first pass aggregated 20 m scene classifications to 60 m cells. Water and subsequent land each had to appear on at least two dates.

The screen produced 18 tile–year candidates for substantial summer-to-summer area loss. The image plate shows the highest-ranked candidate from each of four tiles, with shortwave infrared, near infrared and green mapped to red, green and blue. Seasonal water levels, later refilling, previous changes and coastal settings make a newly formed, permanently drained basin difficult to establish in this sample. No Alaska candidate is reported as a discovery.

The CSV files preserve all 18 candidates and the actual 60 source scene identifiers. Run `python arctic_scan.py` and then `python inspect_lakes.py` from a copy to regenerate the screen and image plate. Dependencies are numpy, pandas, scipy, requests, rasterio, pyproj, matplotlib and certifi. [Sentinel-2 Collection 1 on Earth Search](https://earth-search.aws.element84.com/v1/collections/sentinel-2-c1-l2a) · [Chen et al., historical circumpolar drainage inventory](https://zenodo.org/records/7632013)
