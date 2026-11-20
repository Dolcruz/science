"""Matched-light photometry of the bright surface change at 6.103 S, 276.992 E."""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.colors import TwoSlopeNorm

BASE = Path(__file__).resolve().parent
CHIPS = BASE / '283' / 'check-24'
PAIRS = [('M1405157120RC','M1491897245LC'), ('M1124130817LC','M1481346260RC')]
def masks(x, y):
    yy,xx=np.indices((81,81))
    r=np.hypot(xx-x,yy-y)
    return r<=2.5,(r>=7)&(r<=15)
def contrast(a,x=40,y=40):
    center,ann=masks(x,y)
    if np.any(a[center|ann]<=100):
        return np.nan
    return np.log(a[center]).mean()-np.median(np.log(a[ann]))
def main(chips, output):
    data=np.load(chips/'chips.npz')
    dates=pd.read_csv(chips/'dates.csv').set_index('name')
    fig,axes=plt.subplots(2,3,figsize=(8.8,6.25))
    rows=[]
    for ax,(before,after) in zip(axes,PAIRS):
        a,b=data[before],data[after]
        controls=[(x,y) for y in range(16,66,8) for x in range(16,66,8) if np.hypot(x-40,y-40)>=18]
        for x,y in [(40,40)]+controls:
            value=float(np.expm1(contrast(b,x,y)-contrast(a,x,y)))
            if not np.isfinite(value):
                continue
            rows.append(dict(before=before,after=after,x=x,y=y,target=(x,y)==(40,40),fractional_change=value))
        _,ann=masks(40,40)
        aa=a/np.median(a[ann]);bb=b/np.median(b[ann])
        lim=np.quantile(np.concatenate([aa[22:59,22:59].ravel(),bb[22:59,22:59].ravel()]),[.015,.985])
        for axis,v,n in zip(ax[:2],[aa,bb],[before,after]):
            axis.imshow(v[22:59,22:59],cmap='gray',vmin=lim[0],vmax=lim[1],interpolation='nearest')
            axis.set_title(f"{dates.loc[n,'date']}  ·  {dates.loc[n,'incidence']:.1f}°",fontsize=10)
        ratio=(np.divide(bb,aa,where=aa>0,out=np.full_like(bb,np.nan))-1)*100
        plot=ax[2].imshow(ratio[22:59,22:59],cmap='RdBu_r',norm=TwoSlopeNorm(vmin=-35,vcenter=0,vmax=35),interpolation='nearest')
        ax[2].set_title('Relative change',fontsize=10)
        for axis in ax:
            axis.plot([18,18],[10,13],color='#ffb62e',lw=1.3)
            axis.plot([23,26],[18,18],color='#ffb62e',lw=1.3)
            axis.axis('off')
        ax[0].plot([2,2+5/.92],[32,32],lw=2,color='white')
        ax[0].text(2,31,'5 m',color='white',fontsize=8)
    fig.subplots_adjust(left=.025,right=.91,bottom=.015,top=.935,hspace=.20,wspace=.05)
    cb=fig.colorbar(plot,cax=fig.add_axes([.925,.17,.013,.63]),extend='both',ticks=[-30,-15,0,15,30])
    cb.set_label('Change in normalized brightness (%)',fontsize=8)
    fig.savefig(output/'brightening.png',dpi=175,bbox_inches='tight',pad_inches=.10)
    pd.DataFrame(rows).to_csv(output/'brightness-controls.csv',index=False,lineterminator='\n')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path, nargs='?',
                        help='Read chips.npz and dates.csv here and write the figure and table alongside them.')
    directory = parser.parse_args().directory
    main(directory or CHIPS, directory or BASE)
