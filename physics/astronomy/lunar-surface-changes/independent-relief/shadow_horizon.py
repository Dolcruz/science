"""Test terrain-horizon geometry at the post-impact dark lobes."""
import os
for key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "BLIS_NUM_THREADS"):
    os.environ[key] = "4"

from pathlib import Path
import csv
import numpy as np
from scipy.ndimage import map_coordinates


ROOT = Path(__file__).resolve().parent
DATA = dict(np.load(ROOT/"northwest.npz"))
Y, X = np.mgrid[-23:24,-23:24]
R = np.hypot(X,Y)
MODELS = ["EW","EN","NW"]
PAIRS = [
    ("post_east",89.296,8.632,2),
    ("post_west",270.479,7.379,-2),
    ("postH",91.599,21.139,2),
]
# Local azimuth from north toward east, elevation above the radial tangent plane.
RINGS = [(4.4,7.15),(8,12),(12,18),(16,22)]


def write(name, rows):
    with (ROOT/name).open("w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=rows[0].keys())
        writer.writeheader();writer.writerows(rows)


def height_table():
    output=[]
    basis=np.stack([X*0+1,X,Y],axis=-1)
    for model in MODELS+["dtm_only"]:
        z=DATA["dtm"].astype(float)
        if model != "dtm_only": z+=DATA[model]
        for inner,outer in RINGS:
            mask=(R>=inner)&(R<outer)&np.isfinite(z)
            plane=basis@np.linalg.lstsq(basis[mask],z[mask],rcond=None)[0]
            u=z-plane
            footprint=lambda x: (np.abs(X-x)<=1)&(np.abs(Y)<=2)
            output.append(dict(model=model,inner=inner,outer=outer,floor=np.nanmedian(u[R<1.71]),
                west_5m=np.nanmedian(u[footprint(-5)]),east_5m=np.nanmedian(u[footprint(5)]),
                background_rms=np.sqrt((u[mask]**2).mean())))
    return output


def horizon_table():
    output=[]
    for image,az,el,x0 in PAIRS:
        sun=np.deg2rad(az)
        distances=np.arange(1.,12.01,.25)
        ray_x=distances*np.sin(sun)
        ray_y=-distances*np.cos(sun)
        for model in MODELS:
            # The residuals were measured against the orthorectification DTM.
            # Its actual local terrain slope must be present for a solar-horizon test.
            z=DATA["dtm"]+DATA[model]
            for y in [-1,0,1]:
                for x in [x0-1,x0,x0+1]:
                    zz=map_coordinates(z,np.stack([23+y+ray_y,23+x+ray_x]),order=1,mode="nearest",prefilter=False)
                    base=z[23+y,23+x]
                    if not np.isfinite(base): continue
                    for low in [1,3]:
                        ok=(distances>=low)&np.isfinite(zz)
                        if not ok.any():continue
                        slope=(zz[ok]-base)/distances[ok]
                        imax=np.argmax(slope)
                        output.append(dict(image=image,model=model,x=x,y=y,ray_inner=low,
                            ray_outer=12,sun_az_deg=az,sun_elevation_deg=el,
                            horizon_deg=np.rad2deg(np.arctan(slope[imax])),occluder_distance_m=distances[ok][imax],
                            valid_ray_fraction=ok.sum()/np.sum(distances>=low)))
    return output


def plot_rays():
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1,2,figsize=(8.8,3.2),layout="constrained",sharey=True)
    distance=np.arange(0,12.01,.25)
    for ax,(image,az,el,origin) in zip(axes,PAIRS[:2]):
        alpha=np.deg2rad(az)
        for model,color in zip(MODELS,["#286b99","#c16a2c","#3d8758"]):
            z=DATA["dtm"]+DATA[model]
            floor=z[23,23+origin]
            if not np.isfinite(floor):continue
            sample=map_coordinates(z,np.stack([23-distance*np.cos(alpha),23+origin+distance*np.sin(alpha)]),
                                   order=1,mode="nearest",prefilter=False)
            ax.plot(distance,sample-floor,label=model,color=color,lw=2)
        ax.plot(distance,np.tan(np.deg2rad(el))*distance,"k--",lw=1.3,label="Sun ray")
        ax.axvspan(0,3,color="#999999",alpha=.10)
        ax.axhline(0,color="#888888",lw=.6)
        ax.set(xlim=(0,12),xlabel="Distance toward Sun (m)")
        ax.set_title(f"{'Eastern' if origin>0 else 'Western'} lobe · Sun elevation {el:.2f}°")
        ax.grid(axis="y",alpha=.2)
    axes[0].set_ylabel("Height above central lobe pixel (m)")
    axes[0].legend(ncol=2,fontsize=8,loc="upper left")
    fig.savefig(ROOT/"sightlines.png",dpi=170)
    plt.close(fig)


if __name__=="__main__":
    heights=height_table();horizon=horizon_table()
    plot_rays()
    write("far-field-relief.csv",heights); write("sunward-horizons.csv",horizon)
    for key,az,el,x in PAIRS:
        for model in MODELS:
            r=[t for t in horizon if t["image"]==key and t["model"]==model and t["ray_inner"]==3]
            center=next((t for t in r if t["x"]==x and t["y"]==0),None)
            print(key,model,"central horizon",round(center["horizon_deg"],1) if center else "unmeasured","at",center["occluder_distance_m"] if center else "n/a",
                  "pixels above solar elevation",sum(t["horizon_deg"]>=el for t in r),"/",len(r))
