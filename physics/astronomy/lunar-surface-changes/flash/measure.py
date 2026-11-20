"""Measure calibrated Lunar Reconnaissance Orbiter Narrow Angle Camera cutouts."""
import os
for key in ("OPENBLAS_NUM_THREADS","OMP_NUM_THREADS","MKL_NUM_THREADS","BLIS_NUM_THREADS","NUMEXPR_NUM_THREADS"):
    os.environ[key] = "4"

import json
from pathlib import Path

import cv2
import matplotlib.pyplot as plt

import numpy as np
import pandas as pd

cv2.setNumThreads(4)
ROOT = Path(__file__).resolve().parent
META = json.loads((ROOT / "observations.json").read_text())
SITES = json.loads((ROOT / "sites.json").read_text())
P, Q, T = "M120012567LC", "M1428220502LC", "M1471612432RC"
FEB, JUL = "M183689789LC", "M1129645568LC"
AUG, JAN12, JUL22 = "M1415343880RC", "M181330922LC", "M1412996974RC"
EAST, WEST = "M1521927263LC", "M1527807868RC"
SCALE = 0.7
Y, X = np.mgrid[-50:51, -50:51] * SCALE
R = np.hypot(Y, X)
RING = (R > 11) & (R < 25)
JUL_R = "M1129645568RC"
PAIRS = [(P,Q),(P,T),(FEB,JUL),(FEB,JUL_R),("M186048671RC","M1131999331RC"),(FEB,AUG),(JAN12,JUL22),(Q,T)]
CHRONOLOGY = [
    ("M1134351922RC", "M1210886396RC"), ("M1210886396RC", "M1346065895RC"),
    ("M1210886396RC", "M1361355503RC"), ("M1197927842RC", "M1243829172RC"),
    ("M1197927842RC", EAST), ("M1243829172RC", EAST),
    ("M186048671RC", "M1239124122LC"), ("M1239124122LC", "M1269696510LC"),
    ("M1129645568RC", "M1160269154RC"), ("M1157905715RC", "M1354309624RC"),
]



def fit_change(first, last):
    valid = cv2.erode(((first > 100) & (last > 100)).astype("u1"), np.ones((7,7), "u1")).astype(bool)
    if valid[R < 3].mean() < 1 or valid[RING].mean() < .8:
        return None
    def smooth_log(array):
        return cv2.GaussianBlur(np.log(np.maximum(100, array)), (0,0), .75)
    pre, post = smooth_log(first), smooth_log(last)
    ring = valid & RING
    dy, dx = np.gradient(pre)
    lap = cv2.Laplacian(pre, cv2.CV_32F)
    matrix = np.stack([pre - np.median(pre[ring]), dx, dy, lap, X/15, Y/15, np.ones_like(X)], axis=-1)
    fit = np.linalg.lstsq(matrix[ring], post[ring], rcond=None)[0]
    res = post - matrix @ fit
    return res - np.median(res[ring]), valid


def controls(res, valid):
    values = []
    # Disjoint 3 m radius controls on a 6.3 m grid. All lie outside the central target.
    for dx in range(-36,37,9):
        for dy in range(-36,37,9):
            if not 8 <= SCALE*np.hypot(dx,dy) <= 24:
                continue
            pix = np.hypot(X-SCALE*dx, Y-SCALE*dy) < 3
            if valid[pix].all():
                values.append(res[pix].mean())
    return np.array(values)


def contrast(samples):
    rows = []
    for site, epochs in samples.items():
        pairs = PAIRS + (CHRONOLOGY if site == "northeast_938" else [])
        for first, last in pairs:
            if first not in epochs or last not in epochs:
                continue
            result = fit_change(epochs[first], epochs[last])
            if result is None:
                continue
            res, valid = result
            d = res[R < 3].mean()
            ctrl = controls(res, valid)
            # Signed extremeness in the measured direction. No correction for target selection.
            rows.append(dict(site=site, first=first, last=last, log_change=d,
                             change_percent=100*np.expm1(d), control_n=len(ctrl),
                             control_as_extreme=int(np.count_nonzero(np.sign(d)*ctrl>=abs(d))),
                             control_percent_min=100*np.expm1(ctrl.min()),
                             control_percent_max=100*np.expm1(ctrl.max())))
    return pd.DataFrame(rows)


def figure(samples):
    sites = ["primary","south_2317","south_2610","northeast_938","old_crater"]
    labels = ["18.8 m primary","2.32 km south","2.61 km south","0.94 km NE","Old crater"]
    epochs = [P,FEB,JUL,Q,WEST,EAST]
    fig, axes = plt.subplots(len(sites),len(epochs)+1,figsize=(11,8.6))
    for i,site in enumerate(sites):
        current=samples[site]
        for j,epoch in enumerate(epochs):
            if epoch == JUL and JUL_R in current and site in ["south_2317", "northeast_938"]:
                epoch = JUL_R
            ax=axes[i,j]
            if epoch in current:
                im=current[epoch]
                z=im[(R<24)&(im>100)]
                low,high=np.percentile(z,[1,99])
                ax.imshow(im[26:75,26:75],cmap="gray",vmin=low,vmax=high,interpolation="nearest")
                if i==0 and j==2:
                    ax.plot([3,3+10/SCALE],[44,44],c="white",lw=2)
                    ax.text(3,42,"10 m",color="white",fontsize=7)
                if site not in ["primary","old_crater"]:
                    ax.plot([24,24],[2,8],color="#ffba65",lw=.9)
                    ax.plot([2,8],[24,24],color="#ffba65",lw=.9)
            else:
                ax.set_facecolor("#eeeeee")
                ax.text(.5,.5,"No cutout",ha="center",va="center",size=8,color="#666666",transform=ax.transAxes)
            ax.set_xticks([]); ax.set_yticks([])
            for sp in ax.spines.values(): sp.set_visible(False)
            if j == 0:
                ax.set_ylabel(labels[i],fontsize=9)
            if i == 0:
                heading=META[epoch]["date"]+"\n"+( "east Sun" if epoch == EAST else "west Sun")
                ax.set_title(heading,fontsize=9)
        ax=axes[i,-1]
        pair=(P,Q) if P in current and Q in current else (FEB,JUL)
        res, _ = fit_change(current[pair[0]],current[pair[1]])
        ax.imshow(res[26:75,26:75],cmap="RdBu_r",vmin=-.13,vmax=.13,interpolation="nearest")
        ax.set_xticks([]);ax.set_yticks([])
        for sp in ax.spines.values():sp.set_visible(False)
        if i==0:ax.set_title("Post / pre\nlog residual",size=9)
    fig.subplots_adjust(left=.11,right=.997,bottom=.01,top=.94,wspace=.025,hspace=.07)
    fig.savefig(ROOT/"surface-changes.png",dpi=170,bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    data={s:dict(np.load(ROOT/(s+".npz"))) for s in SITES}
    table=contrast(data)
    table.to_csv(ROOT/"photometry.csv",index=False)
    figure(data)
    print(table.to_string(index=False))
