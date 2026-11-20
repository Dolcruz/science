from images import *
import cv2
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from numpy.linalg import lstsq
import pandas as pd
def run(root,loc,out):
    out.mkdir(parents=True,exist_ok=True);members=json.loads((loc/'centers.json').read_text())
    m=json.loads((root/'observations.json').read_text());setup_geo(m)
    names=sorted(members,key=lambda k:m[k]['date'])
    cuts={}
    for n in names:
        row=members[n];p=np.array([row['x'],row['y']],dtype='f4')
        cuts[n]=cv2.getRectSubPix(np.load(root/'tiles'/(n+'.npy')),(151,151),tuple(p))
    np.savez_compressed(out/'cutouts.npz',**cuts)
    y,x=np.indices((151,151));r=np.hypot(x-75,y-75)
    cols=5;ny=(len(cuts)+cols-1)//cols
    fig,ax=plt.subplots(ny,cols,squeeze=False,figsize=(2.6*cols,2.8*ny),layout='constrained');result=[]
    for c in ax.ravel():c.axis('off')
    for c,n in zip(ax.ravel(),names):
        im=cuts[n];md=m[n]
        if (im[r<12]>100).mean()<.45:continue
        b=np.mean(im[(r>=13)&(r<=25)]);d=im/b
        core=np.log(d[r<=3].mean())
        q=np.percentile(im[55:96,55:96],[1,98]);crop=im[55:96,55:96]
        c.imshow(crop,cmap='gray',interpolation='nearest',vmin=q[0],vmax=q[1]);c.set_title(f"{md['date'][:10]}  i {md['incidence_deg']:.0f}°\n{n}");c.plot([20,20],[8,13],color='c',lw=1);c.plot([27,32],[20,20],color='c',lw=1)
        lons=((md['sun_lon']-276.99227+180)%360)-180
        result.append(dict(product=n,date=md['date'][:10],inc_deg=md['incidence_deg'],sun_from='east' if lons>0 else 'west',log_core=core,med=np.median(im[r<=5])/b,peak=np.max(im[r<=6])/b,low=np.min(im[r<=6])/b))
    pd.DataFrame(result).to_csv(out/'contrast.csv',index=False)
    fig.savefig(out/'sequence.png',dpi=125);plt.close(fig)
    print(pd.DataFrame(result).round(3).to_string(index=False))
if __name__=='__main__':run(*[Path(k) for k in sys.argv[1:]])
