"""Reproduce the field-star comparisons and figures from the archived measurements."""
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.wcs import WCS
from astropy.wcs.utils import proj_plane_pixel_scales


HERE = Path(__file__).resolve().parent
TARGET = "4788303839668784896"
RA, DEC = 68.073988, -47.608994
LOCAL_RUWE = 1.2382092151164348


def read_gaia(name):
    return pd.read_csv(HERE / name, dtype={"source_id": str})


def main():
    cmd = read_gaia("gaia-cmd.csv")
    cmd["absolute_g"] = cmd.phot_g_mean_mag + 5 * np.log10(cmd.parallax) - 10
    target = cmd[cmd.source_id == TARGET].iloc[0]
    field = cmd[cmd.source_id != TARGET]
    twin = target.absolute_g + 2.5 * np.log10(2)
    low_ruwe = field[field.ruwe < LOCAL_RUWE]
    matched_metal = low_ruwe[abs(low_ruwe.mh_gspphot - target.mh_gspphot) < .2]
    controls = read_gaia("gaia-controls.csv")
    controls = controls[controls.source_id != TARGET]
    wide = read_gaia("gaia-field.csv")
    center = SkyCoord(RA, DEC, unit="deg")
    wide["separation_arcsec"] = center.separation(SkyCoord(wide.ra, wide.dec, unit="deg")).arcsec
    wide.sort_values("separation_arcsec").to_csv(HERE / "gaia-neighbors.csv", index=False)
    wis = pd.read_csv(HERE / "irsa-allwise_p3as_psd.csv")
    infrared = wis[wis.designation == "J043217.60-473624.7"].iloc[0]
    wi_pos = SkyCoord(infrared.ra, infrared.dec, unit="deg")
    vhs_pos = SkyCoord(68.073335, -47.606765, unit="deg")
    result = dict(
        target_absolute_g=target.absolute_g, parallax_only_error_mag=5/np.log(10)*target.parallax_error/target.parallax,
        individual_absolute_g_if_twins=twin, cmd_control_count=len(field),
        cmd_control_percentiles_5_50_95=field.absolute_g.quantile([.05,.5,.95]).tolist(),
        faintest_cmd_control=field.absolute_g.max(), controls_fainter_than_individual_twin=int((field.absolute_g >= twin).sum()),
        low_ruwe_metal_matched_controls=len(matched_metal),
        low_ruwe_metal_matched_fainter_than_twin=int((matched_metal.absolute_g >= twin).sum()),
        local_ruwe_threshold=LOCAL_RUWE, ruwe_control_count=len(controls),
        controls_with_equal_or_larger_ruwe=int((controls.ruwe >= target.ruwe).sum()),
        nearby_wise_separation_arcsec=center.separation(wi_pos).arcsec,
        wise_vhs_separation_arcsec=wi_pos.separation(vhs_pos).arcsec)
    (HERE / "comparison.json").write_text(json.dumps(result, indent=2) + "\n")

    fig, axes = plt.subplots(1, 3, figsize=(12, 4), constrained_layout=True)
    ax = axes[0]
    ax.scatter(field.bp_rp, field.absolute_g, s=11, alpha=.45, color="#708094", linewidths=0, label="Local controls")
    ax.scatter(target.bp_rp, target.absolute_g, marker="*", s=175, color="#ae371d", label="TIC 153838604", zorder=3)
    ax.scatter(target.bp_rp, twin, marker="D", s=48, color="#87266e", label="Each equal-light twin", zorder=3)
    ax.set(xlabel="Gaia BP − RP (mag)", ylabel="Observed absolute G (mag)", title="Color–magnitude comparison")
    ax.invert_yaxis()
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    for ax, name, band in zip(axes[1:], ["vhs-j-science.fits", "vhs-ks-science.fits"], ["J", "Ks"]):
        with fits.open(HERE / name) as hdul:
            image = hdul[0].data
            header = hdul[0].header
            wcs = WCS(header)
            x, y = wcs.world_to_pixel(center)
            size = float(np.mean(proj_plane_pixel_scales(wcs))) * 3600
            dx, dy = wcs.world_to_pixel(wi_pos)
            noise = 1.4826*np.median(np.abs(image-np.median(image)))
            display = np.arcsinh((image-np.median(image))/(3*noise))
            ax.imshow(display, origin="lower", cmap="gray", vmin=-.45, vmax=3.9)
            ax.scatter(dx, dy, s=92, facecolors="none", edgecolors="#55e3ee", linewidths=1.1)
            ax.text(dx+4, dy+2, "AllWISE", color="#7ef4ff", fontsize=8)
            ax.set(xlim=(x-14/size,x+14/size), ylim=(y-14/size,y+14/size),
                   title=f"VISTA {band} · FWHM {header['PSF_FWHM']:.2f}″")
            ax.plot([x-11/size,x-6/size],[y-10/size]*2,color="white",lw=2)
            ax.text(x-11/size, y-9/size, "5″", color="white", fontsize=9)
            ax.set_axis_off()
    fig.savefig(HERE / "field-and-infrared.png", dpi=165)
    plt.close(fig)


if __name__ == "__main__":
    main()
