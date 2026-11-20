"""Generate the paper figures from the adjacent TESS analysis and Gaia tables."""
import argparse
from pathlib import Path
import sys

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from batman import _quadratic_ld
from matplotlib.colors import Normalize

HERE = Path(__file__).resolve().parent
OUT = HERE / "figures"
NAVY, TEAL, RED, INK = "#344f69", "#167c83", "#ad4f32", "#202b35"
mpl.rcParams.update({
    "font.family":"DejaVu Sans", "font.size":8.2, "axes.titlesize":9,
    "axes.labelsize":8.2, "axes.edgecolor":"#a8b1b7", "axes.linewidth":.7,
    "xtick.labelsize":7.3, "ytick.labelsize":7.3, "xtick.color":INK, "ytick.color":INK,
    "axes.labelcolor":INK, "axes.titlecolor":INK, "text.color":INK,
    "axes.spines.top":False, "axes.spines.right":False, "pdf.fonttype":42,
})

def save(fig,name):
    fig.savefig(OUT/name,bbox_inches="tight",pad_inches=.045)
    plt.close(fig)

def light_curves(root):
    source=root/"duotransit"
    sys.path.insert(0,str(source))
    from measure import read_sector, fit_event, triangular_profile
    rows=pd.read_csv(source/"measurements.csv")
    fig,axs=plt.subplots(2,2,figsize=(6.3,3.05),sharex=True,sharey=True)
    fig.subplots_adjust(left=.102,right=.99,top=.90,bottom=.14,hspace=.46,wspace=.13)
    for ax,r in zip(axs.flat,rows.itertuples()):
        t,y,_,exp,_,_=read_sector(r.sector,source/"fits")
        mid,depth,dur,x,flux=fit_event(t,y,r.proposed_btjd,exp)
        hours=np.linspace(-3.8,3.8,450)
        curve=-1000*depth*triangular_profile(hours/24+r.proposed_btjd-mid,dur/48,exp)
        ax.axhline(0,color="#cfd6d8",lw=.65)
        ax.scatter(x*24,flux*1000,s=5,edgecolors="none",color=NAVY,alpha=.46)
        ax.plot(hours,curve,c=RED,lw=1.6)
        ax.set_title(f"Sector {r.sector}   |   Cycle {r.cycle}",loc="left",pad=2.5)
        ax.set(xlim=(-3.7,3.7),ylim=(-18.5,6.8),xticks=[-3,-2,-1,0,1,2,3],yticks=[-15,-10,-5,0,5])
    fig.supxlabel("Hours from midpoint predicted from the two published events",fontsize=8.3,y=.008)
    fig.supylabel("Relative flux (ppt)",fontsize=8.3,x=.012)
    save(fig,"tess-eclipses.pdf")

def localization(root):
    import json
    p=root/"duotransit/pixels"
    ds=json.loads((p/"localization.json").read_text())
    fig,axs=plt.subplots(1,2,figsize=(5.25,2.12))
    fig.subplots_adjust(left=.09,right=.85,top=.85,bottom=.22,wspace=.31)
    norm=Normalize(vmin=-.65,vmax=3.1)
    for ax,r in zip(axs,ds):
        im=np.load(p/f"difference_s{r['sector']}.npz")['loss']
        raster=ax.imshow(im,origin="lower",cmap="viridis",norm=norm,interpolation="nearest")
        ax.scatter(*r['expected_xy'],s=76,facecolors='none',edgecolors='white',lw=.9)
        ax.scatter(*r['loss_xy'],marker='+',s=50,c='#ff8661',lw=1.25)
        ax.set(title=f"Sector {r['sector']}  |  CCD {r['ccd']}",xticks=[0,2,4,6,8],yticks=[0,2,4,6,8])
        ax.set_xlabel("Detector column")
    axs[0].set_ylabel("Detector row")
    cb=fig.colorbar(raster,cax=fig.add_axes([.875,.24,.021,.57]))
    cb.set_label("Loss (e$^{-}$ s$^{-1}$ pixel$^{-1}$)",labelpad=5)
    save(fig,"difference-images.pdf")

def model_comparison(root):
    p=root/'companion-vetting'
    models=pd.read_csv(p/'eclipse_models.csv')
    names=["1.20 RJ","0.15 solar radii"]
    fig,axs=plt.subplots(1,2,figsize=(6.35,2.59),gridspec_kw={"width_ratios":[1.2,1]})
    fig.subplots_adjust(left=.088,right=.99,top=.92,bottom=.22,wspace=.40)
    ax=axs[0]
    hours=np.linspace(-1.9,1.9,500)
    for name,col,ls,label in zip(names,[NAVY,RED],["-","--"],["1.20 "+r"$R_{\rm J}$","0.15 "+r"$R_{\odot}$"]):
        r=models[(models.example==name)&(models.u1==.35)].iloc[0]
        z=np.hypot(r.impact,r.speed_Rstar_day*hours/24)
        flux=(_quadratic_ld._quadratic_ld(z,r.k,r.u1,r.u2,1)-1)/(1+r.assumed_flux_ratio)
        ax.plot(hours,1000*flux,ls,c=col,lw=1.65,label=label)
    ax.set(xlabel="Hours from eclipse centre",ylabel="Relative flux (ppt)",ylim=(-14.8,1.2),xlim=(-1.8,1.8))
    ax.legend(frameon=False,fontsize=7,loc="lower left",handlelength=1.7)
    ax.set_title("A  |  Two eclipse profiles",loc='left')
    ax=axs[1]
    d=pd.read_csv(p/'blends/gaia-cmd.csv')
    d=d[d.source_id.astype(str)!='4788303839668784896']
    m=d.phot_g_mean_mag+5*np.log10(d.parallax)-10
    ax.scatter(d.bp_rp,m,s=7.5,c=NAVY,alpha=.40,edgecolors='none')
    ax.scatter(.86393,5.0379,s=37,c=TEAL,zorder=4,label="Observed source",marker="o",edgecolors="white",linewidths=.5)
    ax.scatter(.86393,5.79047,s=32,ec=RED,fc='none',marker='D',zorder=4,label="Equal-light component",linewidths=1.2)
    ax.set(xlabel=r"$G_{\rm BP}-G_{\rm RP}$ (mag)",ylabel=r"$M_G$ (mag)",ylim=(6.12,2.14),xlim=(.819,.911))
    ax.legend(frameon=False,loc="upper right",fontsize=6.8,handletextpad=.3)
    ax.set_title("B  |  Gaia comparison stars",loc='left')
    save(fig,"eclipse-models-cmd.pdf")

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('analysis',nargs='?',type=Path,default=HERE.parent)
    root=parser.parse_args().analysis.resolve()
    OUT.mkdir(exist_ok=True)
    light_curves(root)
    localization(root)
    model_comparison(root)
if __name__=='__main__':
    main()
