# Time reference for the Bochum photometry

The 187 r′ epochs and 186 i′ epochs at this position match distinct observatory frames in the same filter to within 0.472 seconds. The light-curve VOTable labels the photometry times as barycentric TCB, while the archive labels its time coverage as topocentric UTC. An original r′ FITS image records the same MJD as the light curve and gives an observation time of 2011-05-08 23:59:14 UT. The numeric matches favor observatory UTC for this field. [Light-curve metadata](https://dc.g-vo.org/tableinfo/bgds2.lc_r) · [Archive image metadata](https://dc.g-vo.org/tableinfo/bgds.data) · [Selected original FITS header cards](fits-cards.txt) · [Original image](https://dc.g-vo.org/getproduct/bgds/data/gds_big/GDS_0734-2011/r_s/eq010000ms/20110508.comb_avg.0001.fits.fz)

The primary reduction uses the recorded frame time at Cerro Murphy, converts UTC to TDB, and adds the barycentric light-travel correction along the direction of TIC 349414709. The site coordinates are −70.20128° longitude, −24.59867° latitude and elevation 2,817 m. The three nearby stars use the same sky direction for the timing correction. [Observatory coordinates](https://oca.camk.edu.pl/index.php/about/overview/)

## Exposure timing and eclipse depth

The example FITS header labels the time as exposure start, gives a 10-second exposure, and records nine contributing frames. The image table describes its time as a midpoint. The effective photon-weighted midpoint of the combined exposure is uncertain. A shift of five seconds moves one point per band across the fixed eclipse-window boundary. The same close blend near TIC 349414709 dims under all tested conventions. These differences measure sensitivity to the time assignment and sampling.

| Time assignment | In-eclipse counts (r′, i′) | Flux loss (r′, i′) |
|---|---:|---:|
| Recorded frame UTC, barycentric correction | 10, 8 | 10.62%, 10.67% |
| UTC shifted by +5, +45, +90 or +120 s before correction | 9, 7 | 11.54%, 10.77% |
| Time interpreted using the VOTable TCB label | 11, 8 | 9.70%, 10.67% |

Run `python timing/verify.py` from the entry directory to match the photometry to the archived image metadata. The first URL in the source list retrieves the frame table. Run `python measure.py` to regenerate the depth comparisons using the TESS-only ephemeris. [All field frames](frames.csv) · [Source queries and metadata](sources.txt) · [All three stars and both filters](sensitivity.csv)
