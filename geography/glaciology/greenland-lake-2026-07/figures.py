"""Plot co-registered imagery, optical estimates and radar contrasts."""
import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt
from matplotlib.patches import Rectangle
import matplotlib.dates as dates
import numpy as np
import pandas as pd
from scipy import ndimage as nd

from fetch import ROOT, OBS, product_path
from measure import optical


def rgb(o):
    with np.load(product_path(o)) as z:
        a=np.stack([z[k] for k in ["red","green","blue"]],axis=-1).astype(float)
    return np.clip((a*.0001-.1)/.85,0,1)**.70


def plot():
    index={o["id"]:o for o in OBS}
    days=[("20260716","16 July"),("20260720","20 July"),("20260723","23 July")]
    fig,axes=plt.subplots(1,3,figsize=(12,3.8),layout="constrained")
    for ax,(date,label) in zip(axes,days):
        o=index[f"S2C_22WFV_{date}_0_L2A"]
        ax.imshow(rgb(o)[165:515,305:735],extent=[0,4.3,0,3.5])
        ax.add_patch(Rectangle((.15,.15),4,3.2,fill=False,ec="#e7be69",lw=.9))
        ax.set_title(label+" 2026",fontsize=12)
        ax.set_xticks([]);ax.set_yticks([])
        ax.plot([.32,1.32],[.36,.36],lw=3,color="white")
        ax.text(.81,.43,"1 km",color="white",ha="center",fontsize=9)
    fig.suptitle("Filling and loss of exposed water on the Greenland Ice Sheet",fontsize=15)
    fig.supxlabel("Sentinel-2C natural color, identical stretch. Gold outlines enclose the fixed 12.8 km² measurement window. North is up.",fontsize=9)
    fig.savefig(ROOT/"lake-sequence.png",dpi=170)
    plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(8,3.7),layout="constrained")
    for ax,(identifier,label) in zip(axes,[
        ("LC09_L2SP_008013_20260721_02_T1","21 July, 14:55 UTC"),
        ("LC09_L2SP_006013_20260723_02_T1","23 July, 14:43 UTC")]):
        with np.load(product_path(index[identifier])) as raw:
            a=np.stack([raw[k] for k in ["red","green","blue"]],axis=-1).astype(float)
            color=np.clip((a*.0000275-.2)/.85,0,1)**.70
            invalid=(raw["qa_pixel"]&31)>0
            color[invalid]=.45*color[invalid]+np.array([.48,.08,.17])
        ax.imshow(color[58:168,103:243],extent=[0,4.2,0,3.3]);ax.set_xticks([]);ax.set_yticks([])
        ax.set_title(label);ax.plot([.2,1.2],[.2,.2],color="white",lw=2)
        ax.text(.7,.28,"1 km",ha="center",color="white")
    fig.suptitle("Landsat 9 independently records the lake-area loss")
    fig.supxlabel("Identical natural-color stretch. Pink marks pixels excluded by the USGS quality mask.",fontsize=9)
    fig.savefig(ROOT/"landsat-sequence.png",dpi=165);plt.close(fig)

    fig,axes=plt.subplots(1,2,figsize=(9,3.9),layout="constrained")
    z=np.load(ROOT/"measurement-chips.npz")
    for ax,tag,label in zip(axes,["20260722","20260723"],["22 July · 09:36 UTC","23 July · 20:47 UTC"]):
        k=next(k for k in z if tag in k and k.endswith("_hh"))
        a=z[k].astype(float)
        sm=nd.uniform_filter(np.maximum(a,0),3)
        db=10*np.log10(np.maximum(sm,1e-10))
        sl=np.s_[80:260,150:370]
        ax.imshow(db[sl],cmap="gray",vmin=-25,vmax=-7,extent=[0,4.4,0,3.6])
        ax.contour(z["radar_foot"][sl].astype(float),[.5],origin="upper",extent=[0,4.4,0,3.6],colors="#e9c265",linewidths=.55)
        ax.set_title(label)
        ax.set_xticks([]);ax.set_yticks([]);ax.plot([.25,1.25],[.2,.2],lw=3,color="white");ax.text(.75,.26,"1 km",ha="center",color="white")
    fig.suptitle("Radar contrast across the 20 July water footprint",fontsize=14)
    fig.supxlabel("Sentinel-1 HH terrain-corrected backscatter. Both images use −25 to −7 dB. Color outlines follow the optical footprint.",fontsize=8)
    fig.savefig(ROOT/"radar-sequence.png",dpi=170)
    plt.close(fig)

    fig,ax=plt.subplots(figsize=(8.1,5.3),layout="constrained")
    q=pd.read_csv(ROOT/"optical.csv");q["time"]=pd.to_datetime(q.time,utc=True)
    for name,group,color,mark in [("Sentinel-2",q.id.str.startswith("S2"),"#157687","o"),("Landsat",q.id.str.startswith("L"),"#bf642c","s")]:
        t=q[group&(q.clear_fraction>=.99)].sort_values("time")
        ax.errorbar(t.time,t["water_km2_0.25"],yerr=[t["water_km2_0.25"]-t["water_km2_0.30"],t["water_km2_0.20"]-t["water_km2_0.25"]],color=color,marker=mark,ls="none",label=name,capsize=3)
    partial=q[q.id.eq("LC09_L2SP_008013_20260721_02_T1")].iloc[0]
    ax.scatter([partial.time],[partial["water_km2_0.25"]],marker="^",s=60,c="#bf642c",label="Landsat lower bound (72% clear)")
    ax.set_ylabel("Exposed water within the basin window (km²)");ax.set_xlabel("July 2026 (UTC)")
    ax.xaxis.set_major_formatter(dates.DateFormatter("%d"));ax.grid(axis="y",alpha=.25)
    bx=ax.twinx();r=pd.read_csv(ROOT/"radar.csv").query("coverage>=0.99").copy()
    r["time"]=pd.to_datetime(r.time,utc=True)
    bx.plot(r.time,100*r["foot_below_4.5dB"],"--d",lw=1,ms=4,color="#674890",label="Sentinel-1 dark fraction")
    bx.set_ylabel("Radar-dark fraction of peak footprint (%)",color="#674890");bx.set_ylim(-3,105)
    handles,labels=ax.get_legend_handles_labels();h2,l2=bx.get_legend_handles_labels()
    ax.legend(handles+h2,labels+l2,loc="upper right",fontsize=8)
    ax.set_title("Optical area and all-weather radar response",fontsize=14)
    fig.savefig(ROOT/"chronology.png",dpi=155);plt.close(fig)

    o=index["S2C_22WFV_20260723_0_L2A"];fig,ax=plt.subplots(figsize=(8,5),layout="constrained")
    ax.imshow(rgb(o),extent=[0,13.2,0,7.8]);ax.add_patch(Rectangle((3.2,2.8),4,3.2,fill=False,ec="#ffca67",lw=1.5))
    controls=pd.read_csv(ROOT/"controls.csv");c=controls[controls.id==o["id"]]
    for k in c.itertuples():
        x=(k.x+.5)*.01;y=7.8-(k.y+.5)*.01
        ax.plot(x,y,"o",mfc="none",mec="#5ef8e7",ms=9)
        ax.annotate(f"{100*k.water_fraction:.0f}%",(x,y),xytext=(6,4),textcoords="offset points",color="#e8ffff",fontsize=8,weight="bold")
    ax.set_xlabel("Easting offset (km)");ax.set_ylabel("Northing offset (km)")
    ax.set_title("Water retained in neighboring pool interiors on 23 July")
    fig.supxlabel("Percentages refer to 120 m radius disks selected from the 20 July image. Gold marks the area-measurement window.",fontsize=8)
    fig.savefig(ROOT/"comparison-pools.png",dpi=155);plt.close(fig)


if __name__=="__main__":
    plot()
