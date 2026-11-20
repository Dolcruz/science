"""Render the same lunar ground before and after the McGetchin impact."""
from pathlib import Path
import argparse
import numpy as np
from matplotlib import pyplot as plt

base=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--full-rasters',type=Path,help='Directory of registered.npz and opposing-relief.npz from the field analysis')
args=parser.parse_args()
if args.full_rasters:
    sl=np.s_[337:384,206:253]
    with np.load(args.full_rasters/'registered.npz') as day, np.load(args.full_rasters/'opposing-relief.npz') as night:
        np.savez_compressed(base/'wall-cutouts.npz',east_before=day['pre10'][sl],east_after=day['postH'][sl],west_before=night['pre_west'][sl],west_after=night['post_west'][sl])
data=np.load(base/'wall-cutouts.npz')
fig,axes=plt.subplots(2,2,figsize=(7.6,7.0))
yy,xx=np.indices((47,47))-23
ring=(np.hypot(xx,yy)>12)&(np.hypot(xx,yy)<22)
for i,(sun,dates) in enumerate([('east',['9 Dec 2010','22 Jan 2026']),('west',['22 Mar 2019','30 Jul 2026'])]):
    pair=[data[sun+'_'+n] for n in ['before','after']]
    pair=[v/np.median(v[ring]) for v in pair]
    lo,hi=np.percentile(np.stack(pair)[:,4:-4,4:-4],[1,98.5])
    for j,(a,date) in enumerate(zip(pair,dates)):
        ax=axes[i,j]
        ax.imshow(a[4:-4,4:-4],vmin=lo,vmax=hi,interpolation='nearest',cmap='gray')
        ax.set_title(date,fontsize=11,pad=4)
        ax.plot([19,19],[9.7,13.2],color='#ffb942',lw=1.4)
        ax.plot([25,28.5],[19,19],color='#ffb942',lw=1.4)
        ax.text(1.2,35.5,'5 m',color='white',fontsize=8,bbox=dict(facecolor='#242424',alpha=.7,edgecolor='none',pad=.7))
        ax.plot([1.3,6.3],[37,37],color='white',lw=2.3)
        ax.set_xticks([]);ax.set_yticks([])
        for edge in ax.spines.values():edge.set_visible(False)
        if j==0:ax.set_ylabel('Sun from the '+sun,fontsize=10)
for j,s in enumerate(['Before','After']):
    axes[0,j].text(.5,1.17,s,ha='center',va='center',fontsize=14,weight='bold',transform=axes[0,j].transAxes)
fig.subplots_adjust(left=.07,right=.99,top=.90,bottom=.014,hspace=.11,wspace=.035)
fig.savefig(base/'mcgetchin-walls.png',dpi=175,bbox_inches='tight',pad_inches=.08)
