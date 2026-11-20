"""Check the detector footprint and compare independent SPOC aperture photometry."""
import hashlib
import io
import json
import zipfile
from urllib.parse import urlencode
from urllib.request import urlopen

from astropy.io import fits
import numpy as np

from parity import OUT, PRIMARY, fit_event, write_rows


def download(url):
    with urlopen(url) as response:
        return response.read()


def main():
    query={"ra":68.073987,"dec":-47.608987}
    api="https://mast.stsci.edu/tesscut/api/v0.1/"
    footprint=api+"sector?"+urlencode(query)
    inventory=json.loads(download(footprint))
    cut=api+"astrocut?"+urlencode(dict(query,x=9,y=9,units="px",sector=30))
    with zipfile.ZipFile(io.BytesIO(download(cut))) as z:
        raw=z.read(next(n for n in z.namelist() if n.endswith('.fits')))
    with fits.open(io.BytesIO(raw)) as h:
        hdr=h[1].header
        x0=hdr['1CRV5P']+(1-hdr['1CRP5P'])*hdr['1CDL5P']
        y0=hdr['2CRV5P']+(1-hdr['2CRP5P'])*hdr['2CDL5P']
        cube=h[1].data["FLUX"]
        source=dict(footprint_url=footprint,footprint=inventory["results"],
                    s30_cutout_url=cut,s30_lower_left_detector_xy=[x0,y0],
                    s30_detector_columns=[x0,x0+cube.shape[2]-1],
                    s30_science_column_range=[45,2092],s30_median_image_range_e_per_s=[
                        float(np.nanmin(np.nanmedian(cube,axis=0))),float(np.nanmax(np.nanmedian(cube,axis=0)))])
    (OUT/'footprint.json').write_text(json.dumps(source,indent=2),encoding='utf-8')
    comparisons=[]
    for s in [4,5,31,32]:
        name=f"hlsp_tess-spoc_tess_phot_0000000153838604-s{s:04d}_tess_v1_lc.fits"
        url=f"https://archive.stsci.edu/hlsps/tess-spoc/s{s:04d}/target/0000/0001/5383/8604/{name}"
        raw=download(url)
        with fits.open(io.BytesIO(raw)) as h:
            d=h[1].data;hdr=h[1].header
            row=dict(sector=s,crowdsap=hdr['CROWDSAP'],flfrcsap=hdr['FLFRCSAP'],sha256=hashlib.sha256(raw).hexdigest(),url=url)
            for key in ['SAP_FLUX','PDCSAP_FLUX']:
                depth=None
                if s in PRIMARY['sector']:
                    mid=float(PRIMARY[PRIMARY['sector']==s]['fitted_btjd'][0])
                    valid=np.isfinite(d[key])&np.isfinite(d['TIME'])&(d['QUALITY']==0)
                    _,depth,*_=fit_event(d['TIME'][valid],d[key][valid],mid,hdr['TIMEDEL'])
                    depth=1000*depth
                row[key+'_depth_ppt']=depth
            comparisons.append(row)
    write_rows('spoc_apertures.csv',comparisons)


if __name__=="__main__":
    main()
