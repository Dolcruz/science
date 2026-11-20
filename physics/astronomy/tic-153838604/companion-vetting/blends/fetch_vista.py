"""Recreate the two science-only VISTA cutouts from the ESO SODA service."""
import hashlib
from io import BytesIO
from pathlib import Path

import requests
from astropy.io import fits
from astropy.wcs import WCS


HERE = Path(__file__).resolve().parent
SERVICE = "https://dataportal.eso.org/dataPortal/soda/sync"
CIRCLE = "68.073988 -47.608994 0.0125"
PRODUCTS = {
    "j": ("ADP.2014-12-22T15:01:36.920", "f85363efab1c6e7a895f133bb0a9e4d0d70f003a3251ce2b6644c4bdef4fdf4e"),
    "ks": ("ADP.2014-12-22T14:57:22.100", "280a1d36417a295bbcabfdec53ed8dc7bee1e12884bb00f9013147b0ae535cfb"),
}


def save_science_plane(band, raw, directory):
    product, expected = PRODUCTS[band]
    with fits.open(BytesIO(raw)) as hdul:
        chip = hdul[1]
        # A fixed byte order makes the decoded count-array hash portable.
        data = chip.data.astype(">f8")
        if hashlib.sha256(data.tobytes()).hexdigest() != expected:
            raise ValueError(f"The ESO {band} science array differs from the archived measurement.")
        header = WCS(chip.header).to_header(relax=True)
        for key in ["PSF_FWHM", "BUNIT", "DATE-OBS", "MJD-OBS", "EXPTIME"]:
            header[key] = chip.header[key]
        header["FILTER"] = band.upper()
        header["ARCFILE"] = product
        fits.PrimaryHDU(data, header).writeto(directory / f"vhs-{band}-science.fits", overwrite=True)


if __name__ == "__main__":
    for band, (product, _) in PRODUCTS.items():
        response = requests.get(SERVICE, params={"ID": "ivo://eso.org/ID?" + product, "CIRCLE": CIRCLE})
        response.raise_for_status()
        save_science_plane(band, response.content, HERE)
