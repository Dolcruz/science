# Archive queries

The field center is ICRS (68.073988Â°, âˆ’47.608994Â°), the Gaia DR3 source ID is 4788303839668784896, and the primary catalog snapshots were retrieved on 20 November 2026. Angular radii define the astrophysical comparison fields. The returned rows and original catalog column headers are stored alongside this file.

## European Space Agency Gaia Archive

Run the following queries against the [Gaia TAP service](https://gea.esac.esa.int/tap-server/tap). The direct source, parameters and orbit queries use the archived column names. The full 90-arcsecond Gaia field is in `gaia-field.csv`.

```sql
SELECT * FROM gaiadr3.gaia_source WHERE source_id=4788303839668784896
SELECT * FROM gaiadr3.astrophysical_parameters WHERE source_id=4788303839668784896
SELECT * FROM gaiadr3.nss_two_body_orbit WHERE source_id=4788303839668784896

SELECT source_id,ra,dec,phot_g_mean_mag,bp_rp,parallax,parallax_error,pmra,pmdec,ruwe
FROM gaiadr3.gaia_source
WHERE 1=CONTAINS(POINT('ICRS',ra,dec),CIRCLE('ICRS',68.073988,-47.608994,0.025))
```

The controls for astrometric quality are within 0.5 mag in G and 0.15 mag in BPâˆ’RP. The target was removed from the reference sample.

```sql
SELECT source_id,ruwe,phot_g_mean_mag,bp_rp,astrometric_excess_noise,ipd_frac_multi_peak
FROM gaiadr3.gaia_source
WHERE 1=CONTAINS(POINT('ICRS',ra,dec),CIRCLE('ICRS',68.073988,-47.608994,3))
AND phot_g_mean_mag BETWEEN 12.424309 AND 13.424309
AND bp_rp BETWEEN 0.71393 AND 1.01393
AND astrometric_params_solved=31 AND visibility_periods_used>=9
```

The colorâ€“magnitude reference is independently selected in position, color and parallax. The high signal-to-noise criteria use the parallax and both Gaia color fluxes. Giants and binaries can enter this reference population.

```sql
SELECT source_id,phot_g_mean_mag,bp_rp,parallax,parallax_error,ruwe,
       ag_gspphot,teff_gspphot,mh_gspphot,logg_gspphot
FROM gaiadr3.gaia_source
WHERE 1=CONTAINS(POINT('ICRS',ra,dec),CIRCLE('ICRS',68.073988,-47.608994,3))
AND parallax BETWEEN 2 AND 3.333333333
AND bp_rp BETWEEN 0.8239326 AND 0.9039326
AND parallax_over_error>20 AND phot_bp_mean_flux_over_error>30
AND phot_rp_mean_flux_over_error>30 AND astrometric_params_solved=31
```

The GaiaUnlimited `BinarySystemsSelectionFunction.query_RUWE` method uses ICRS HEALPix level 5 in RING ordering. Index 10685 has center (69.107143Â°, âˆ’48.141208Â°). The released `dict_SL_ruwe.pkl` record gives `ruwe_threshold=1.2382092151164348` and `ruwe_simulation=1.1672672672672673`. The analysis uses the former. The archive file SHA-256 is `afb04170070ae037bbe33a0a09ddc3d83a6810fc3b195bc2042e2afa78ac7e3e`. [Official GaiaUnlimited example](https://gaiaunlimited.readthedocs.io/en/stable/notebooks/dr3-unresolved-binaries.html) Â· [Data release](https://zenodo.org/records/11102437)

## Image and catalog queries

* The [ESO ObsCore archive](https://archive.eso.org/tap_obs/) query used `WHERE 1=CONTAINS(POINT('ICRS',68.073988,-47.608994),s_region)` on `ivoa.ObsCore`. Each original VISTA cutout is a [SODA sync request](https://dataportal.eso.org/dataPortal/soda/sync) with `CIRCLE=68.073988 -47.608994 0.0125`. The `ID` values are `ivo://eso.org/ID?ADP.2014-12-22T15:01:36.920` (J) and `ivo://eso.org/ID?ADP.2014-12-22T14:57:22.100` (Ks). The dates in the product IDs are processing dates. The packaged science planes preserve every decoded pixel value, the WCS, observation date, exposure, units and measured FWHM. Run `python fetch_vista.py` to regenerate both from ESO. The script verifies SHA-256 for each 264 × 264 array encoded as row-major big-endian IEEE float64. The hashes are `f85363efab1c6e7a895f133bb0a9e4d0d70f003a3251ce2b6644c4bdef4fdf4e` (J) and `280a1d36417a295bbcabfdec53ed8dc7bee1e12884bb00f9013147b0ae535cfb` (Ks). Successive ESO requests change the server creation date and raw FITS checksum. The scientific array hashes are stable. [ESO archive](https://archive.eso.org/)
* The [VizieR catalog server](https://vizier.cds.unistra.fr/viz-bin/asu-tsv) queries use the common center and a 10-arcsecond cone (`-c.rs=10`, `-out.all=1`). The individual catalog identifiers are `II/367/vhs_dr5`, `II/371/des_dr2`, `J/AJ/159/19`, `J/AJ/162/192` and `B/wds/wds`. The raw TSV files retain epochs, error flags and descriptions. [VizieR](https://vizier.cds.unistra.fr/)
* Using [IRSA TAP](https://irsa.ipac.caltech.edu/TAP/), select the columns in the two corresponding CSV headers from `fp_psc` and `allwise_p3as_psd`, with `WHERE 1=CONTAINS(POINT('ICRS',ra,dec),CIRCLE('ICRS',68.073988,-47.608994,0.002778))`. The cone is 10.00 arcseconds. [IPAC IRSA](https://irsa.ipac.caltech.edu/)
* The MAST request used service `Mast.Caom.Cone` centered on the target with radius 0.001 degrees, returning 40 records. The archive's pagination records report 40 rows and one page. The saved subset in `mast-coverage.json` retains collection, instrument, observation ID and observation dates. [MAST portal](https://mast.stsci.edu/portal/Mashup/Clients/Mast/Portal.html)
* The nearby-target CSV, file-list CSV and upload inventory are included. The extractions refer to TIC 153838604. The three CSVs preserve the public inventory on the retrieval date. [ExoFOP target record](https://exofop.ipac.caltech.edu/tess/target.php?id=153838604)
