# Flash and spacecraft records near 6.103°S, 276.992°E

A surface change near the Moon's western limb is bracketed by orbital images on 10 November 2022 and 13 March 2023. NELIOTA flash 283 is only 6.95 km from the measured site at the precision of the published flash coordinates, but it occurred on 25 May 2023, 73 calendar days after the March image already shows the feature. This chronology rules out the May flash as the event that produced the observed change. The [public NELIOTA event record](https://neliota.astro.noa.gr/LIFDatabase/EventDetails/363) identifies the 0.231 s, two-camera detection at 20:34:28.000 UT and gives 5.9°S, 82.9°W. The paper gives 20:34:27.999 UT. No subpixel terrestrial astrometric refinement is needed for this temporal exclusion.

## Events during the image interval

| Source | Coverage and result |
|---|---|
| NELIOTA, validated and suspected | Table 1 gives 19 consecutive entries (252–270). The nearest was validated event 261 at 0.2°N, 66.5°W, on 26 December 2022, **535.0 km** from the site. [Liakos et al.](https://arxiv.org/abs/2403.19613) |
| Public Lunar Impact Flashes Database | Ten validated records lie in the date interval. All ten are NELIOTA detections also present in the published table. The website accepts external observers and exposes only validated events to anonymous users. [LIF Database](https://neliota.astro.noa.gr/LIFDatabase) |
| 26 January 2023, Nice and Melazzo | The independently recorded 20:33:30.96 UT flash was placed near 23.79°N, 31.36°W, approximately 1,776 km away. [UAI localization](https://www.uai.it/sito/news/uai-ricerca/il-probabile-impatto-lunare-del-26-gennaio-2023-registrato-dalla-sezione-nazionale-di-ricerca-luna-uai/) and [two-station analysis](https://academic.oup.com/mnras/article/529/4/3828/7274824) |
| 23 February 2023, Hiratsuka | Daichi Fujii placed the 11:14:30.8 UT flash near Ideler L. The IAU center of that named feature is 49.33°S, 23.65°E, about 2,912 km from the western-limb site. This distance refers to the named landmark. [Observer's location report](https://x.com/dfuji1/status/1629261104588398592) and [IAU Gazetteer](https://planetarynames.wr.usgs.gov/Feature/10118) |
| Spacecraft hardware | The 14 August 2026 LROC PDS release contains 71 objects and zero dated arrivals during the interval. Both it and NASA's spacecraft chronology place the adjacent known impacts on 4 March 2022 (rocket body) and 25 April 2023 (Hakuto-R Mission 1). [LROC PDS product](https://data.lroc.im-ldi.com/lroc/view_rdr/SHAPEFILE_ANTHROPOGENIC_OBJECTS) and [NASA NSSDCA chronology](https://nssdc.gsfc.nasa.gov/planetary/lunar/lunar_artifact_impacts.html) |

No record examined identifies a source for this surface change. Telescopes observe limited lunar terrain, lighting conditions and times. LROC explicitly excludes some spacecraft objects that have yet to be located in its images. The absence of a recorded flash or known landing does not determine the physical cause of the change.

## Reproduction

The published and online event tables provide dates, classes and positions. The two CSV files preserve the in-window records and the nearby May event for comparison. Run `python verify.py` to recalculate the spherical distances, the 73-day offset and the date match against the PDS shapefile. The script uses a lunar radius of 1,737.4 km. It downloads the public hardware archive and records the retrieved file's SHA-256 digest. The computation uses Python's standard library and introduces no network timeout or retry loop.

The Lunar Impact Flashes Database was developed by the NELIOTA project with funding from ESA during its first two phases and from the European Union's Horizon Europe Programme during its third phase, with ESA implementation. NELIOTA observations used the 1.2 m Kryoneri telescope in Greece, operated by the Institute for Astronomy, Astrophysics, Space Applications and Remote Sensing of the National Observatory of Athens.
