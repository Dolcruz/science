"""Public spectroscopy metadata for TIC 153838604. Write a dated snapshot to stdout."""
from collections import Counter
import csv
from datetime import datetime, timezone
from io import StringIO
import json
from math import cos, radians
from urllib.parse import urlencode
from xml.etree import ElementTree

import requests


RA = 68.07398831987392
DEC = -47.60899384364195
SOURCE = 4788303839668784896
ESAC = "https://gea.esac.esa.int/tap-server/tap/sync"
ESO = "https://archive.eso.org/tap_obs/sync"
GES = "https://archive.eso.org/tap_cat/sync"
GALAH = "https://datacentral.org.au/vo/tap/sync"
LCO = "https://archive-api.lco.global/frames/"
results = []


def rows(response):
    raw = response.text.strip()
    if raw.startswith("<"):
        root = ElementTree.fromstring(raw)
        if root.find(".//{*}INFO[@value='ERROR']") is not None:
            raise ValueError(root.find(".//{*}INFO[@value='ERROR']").text)
        if root.find(".//{*}INFO[@value='OVERFLOW']") is not None:
            raise ValueError("Truncated TAP query")
        cols = [f.attrib["name"] for f in root.findall(".//{*}FIELD")]
        return [dict(zip(cols, [c.text for c in row])) for row in root.findall(".//{*}TR")]
    return list(csv.DictReader(StringIO(raw.removeprefix("#Table1").lstrip())))


def query(label, url, params, parse, payload=None):
    try:
        if payload is None:
            response = requests.get(url, params=params)
        else:
            response = requests.post(url, params=params, json=payload)
        record = {"name":label, "url":response.url, "http_status":response.status_code}
        if payload:
            record["POST_json"] = payload
        if response.ok:
            record["result"] = parse(response)
        else:
            record["coverage"] = "unknown"
    except (requests.RequestException, ValueError, KeyError) as error:
        record = {"name":label, "url":url+"?"+urlencode(params), "error":type(error).__name__, "coverage":"unknown"}
    results.append(record)


def tap(label, endpoint, sql, parse=rows):
    query(label,endpoint,{"REQUEST":"doQuery","LANG":"ADQL","FORMAT":"csv","QUERY":sql},parse)


def box(ra, dec, arcsec):
    # The rectangular prefilter contains the sky cone, including proper-motion displacement.
    half = arcsec/3600 + 0.00001
    dra = half/cos(radians(abs(DEC)+half))
    return (f"{ra} BETWEEN {RA-dra} AND {RA+dra} AND "
            f"{dec} BETWEEN {DEC-half} AND {DEC+half}")


def frames(response):
    counts = Counter()
    while True:
        page = response.json()
        counts.update(f"{r['instrument_id']} / {r['configuration_type']}" for r in page["results"])
        if not page["next"]:
            return {"frames":sum(counts.values()),"instrument_and_type":dict(counts)}
        response = requests.get(page["next"])
        response.raise_for_status()


def noir(response):
    data = response.json()
    if data[0].get("RESULTS",{}).get("MORE"):
        raise ValueError("Archive reports additional results")
    products = Counter(r["instrument"] for r in data[1:])
    return {"rows":len(data)-1,"instruments":dict(products),
            "archive_parameters":data[0].get("PARAMETERS",{})}


def main():
    rv_cols = ("source_id,ra,dec,pmra,pmdec,phot_g_mean_mag,grvs_mag,rv_method_used,"
               "radial_velocity,radial_velocity_error,rv_nb_transits,rv_nb_deblended_transits,"
               "rv_visibility_periods_used,rv_expected_sig_to_noise,rv_time_duration,"
               "rv_amplitude_robust,rv_chisq_pvalue,rv_renormalised_gof,has_epoch_rv,"
               "has_rvs,has_xp_continuous,non_single_star")
    tap("Gaia DR3 RVS",ESAC,f"SELECT {rv_cols} FROM gaiadr3.gaia_source WHERE source_id={SOURCE}")
    tap("Gaia DR2 RVS",ESAC,"SELECT source_id,radial_velocity,radial_velocity_error,rv_nb_transits "
        f"FROM gaiadr2.gaia_source WHERE source_id={SOURCE}")
    for schema in ["gaiadr3","gaiafpr"]:
        tap(schema+" RV epochs",ESAC,f"SELECT COUNT(*) AS n FROM {schema}.vari_epoch_radial_velocity "
            f"WHERE source_id={SOURCE}")
    tap("Gaia DR3 BP/RP mean spectrum",ESAC,
        f"SELECT * FROM gaiadr3.xp_summary WHERE source_id={SOURCE}")
    tap("Gaia public schemas",ESAC,"SELECT schema_name FROM tap_schema.schemas")
    for table in ["galah_dr3.main_spec","galah_dr4.mainspectable"]:
        tap(table,GALAH,f"SELECT COUNT(*) AS n FROM {table} WHERE "+box("ra","dec",60))
    tap("GALAH DR4 Gaia identifier",GALAH,"SELECT COUNT(*) AS n FROM galah_dr4.mainspectable "
        f"WHERE gaiadr3_source_id={SOURCE}")
    for table in ["safcat.GES_DR5_1_V1","safcat.GES_2021_VRAD"]:
        tap(table,GES,f"SELECT COUNT(*) AS n FROM {table} WHERE "+box("RA","DECLINATION",60))
    tap("RAVE DR6 observations","https://www.rave-survey.org/tap/sync",
        "SELECT COUNT(*) AS n FROM ravedr6.dr6_obsdata WHERE "
        f"1=CONTAINS(POINT('ICRS',ra_input,dec_input),CIRCLE('ICRS',{RA},{DEC},{1/60}))")
    for table in ["apogeeStar","apogeeVisit"]:
        query("APOGEE DR17 "+table,"https://skyserver.sdss.org/dr17/SkyServerWS/SearchTools/SqlSearch",
              {"cmd":f"SELECT COUNT(*) AS n FROM {table} WHERE "+box("ra","dec",60),"format":"csv"},rows)
    query("SDSS DR20 Valis","https://api.sdss.org/valis/query/cone",
          {"ra":RA,"dec":DEC,"radius":1/60,"units":"degree","release":"DR20"},lambda r:r.json())
    for ra,dec in [("ra","dec"),("ra_pnt","dec_pnt")]:
        tap("ESO raw science "+ra,ESO,f"SELECT target,instrument,dp_tech,dp_id FROM dbo.raw "
            f"WHERE dp_cat='SCIENCE' AND "+box(ra,dec,300))
    tap("ESO raw science footprint",ESO,"SELECT instrument,dp_tech,COUNT(*) AS n FROM dbo.raw "
        f"WHERE dp_cat='SCIENCE' AND 1=CONTAINS(POINT('ICRS',{RA},{DEC}),s_region) "
        "GROUP BY instrument,dp_tech")
    tap("ESO ObsCore centers",ESO,"SELECT target_name,instrument_name,dataproduct_type,dp_id "
        "FROM ivoa.ObsCore WHERE "+box("s_ra","s_dec",300))
    tap("ESO ObsCore footprint",ESO,"SELECT instrument_name,dataproduct_type,COUNT(*) AS n "
        f"FROM ivoa.ObsCore WHERE 1=CONTAINS(POINT('ICRS',{RA},{DEC}),s_region) "
        "GROUP BY instrument_name,dataproduct_type")
    query("ExoFOP spectroscopy","https://exofop.ipac.caltech.edu/tess/target.php",
          {"id":"153838604","json":""},lambda r:{"TIC":r.json()["basic_info"]["tic_id"],
           "spectroscopy":r.json()["spectroscopy"],"files":r.json()["files"]})
    query("LCO footprint",LCO,{"covers":f"POINT({RA} {DEC})","pagination_style":"cursor"},frames)
    for alias in ["153838604","04321774-4736316","212-004500"]:
        query("LCO spectrum name "+alias,LCO,{"target_name":alias,"configuration_type":"SPECTRUM",
              "pagination_style":"cursor"},frames)
    query("NOIRLab coverage","https://astroarchive.noirlab.edu/api/sia/voimg",
          {"POS":f"{RA},{DEC}","SIZE":5/60,"VERB":3,"format":"json"},noir)
    half = 5/60
    dra = half/cos(radians(abs(DEC)+half))
    query("NOIRLab CHIRON centers","https://astroarchive.noirlab.edu/api/adv_search/find/",
          {"format":"json","rectype":"file"},noir,
          {"outfields":["original_filename","instrument","obs_type","prod_type","ra_center","dec_center"],
           "search":[["ra_center",RA-dra,RA+dra],["dec_center",DEC-half,DEC+half],["instrument","chiron"]]})
    query("Gemini pointings",f"https://archive.gemini.edu/jsonsummary/ra={RA:.6f}/dec={DEC:.6f}/sr=300",
          {},lambda r:{"rows":len(r.json())})
    print(json.dumps({"accessed_utc":datetime.now(timezone.utc).isoformat(),
                      "target":"TIC 153838604","queries":results},indent=2))


if __name__=="__main__":
    main()
