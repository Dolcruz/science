"""Retrieve the original survey products and re-extract compact measurement inputs."""
import argparse
from pathlib import Path
from urllib.request import urlopen

import numpy as np
import pandas as pd
from astropy.io import fits
from astropy.table import Table
from astropy.wcs import WCS

ROOT = Path(__file__).resolve().parent


def difference_images(hdus, out):
    tab = hdus[1].data
    t, flux = tab['TIME'], tab['FLUX']
    good = np.isfinite(t) & (tab['QUALITY'] == 0)
    epoch, period = 4293.69156, 2.70917248
    first, last = np.rint((np.array([t[good].min(), t[good].max()])-epoch)/period).astype(int)
    images = []
    for n in range(first, last+1):
        dt = t-(epoch + n*period)
        core = good & (abs(dt) < .023)
        left = good & (dt > -.115) & (dt < -.07)
        right = good & (dt > .07) & (dt < .115)
        wing = left | right
        if core.sum() >= 8 and wing.sum() >= 16 and left.any() and right.any():
            images.append(np.median(flux[wing],axis=0)-np.median(flux[core],axis=0))
    yy, xx = np.indices(flux.shape[1:])
    ra, dec = WCS(hdus[2].header).all_pix2world(xx, yy, 0)
    np.savez_compressed(out/'difference-images.npz', events=images, ra_deg=ra, dec_deg=dec)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('cache', type=Path, help='Directory for downloaded FITS and VOTable files')
    parser.add_argument('--output', type=Path, default=ROOT)
    args = parser.parse_args()
    args.cache.mkdir(exist_ok=True, parents=True)
    args.output.mkdir(exist_ok=True, parents=True)
    ground, curves = [], {}
    for r in pd.read_csv(ROOT/'source-products.csv').itertuples():
        optical = r.product.startswith('BGDS')
        path = args.cache/(r.product+'.xml' if optical else r.product)
        if not path.exists():
            with urlopen(r.url) as response:
                data = response.read()
            path.write_bytes(data)
        if optical:
            tab = Table.read(path, format='votable')
            band = r.product.split('-')[3]
            ground.extend((r.target, band, float(t), float(m), float(e)) for t,m,e in
                          zip(tab['obs_time'], tab['phot'], tab['mag_error']))
        else:
            with fits.open(path) as hdus:
                if r.product.endswith('_tp.fits'):
                    difference_images(hdus, args.output)
                    continue
                sector, d = hdus[0].header['SECTOR'], hdus[1].data
                col = next(k for k in ('PDCSAP_FLUX','DET_FLUX','KSPSAP_FLUX') if k in d.names)
                t, f = d['TIME'], d[col]
                good = (d['QUALITY'] == 0) & np.isfinite(t) & np.isfinite(f)
                curves[f'time{sector}'] = t[good].astype('float64')
                curves[f'flux{sector}'] = (f[good]/np.median(f[good])).astype('float32')
    pd.DataFrame(ground, columns=['source','band','mjd_tcb','mag','mag_err']).to_csv(
        args.output/'bochum-curves.csv', index=False)
    np.savez_compressed(args.output/'tess-curves.npz', **curves)


if __name__ == '__main__':
    main()
