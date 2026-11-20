from survey import setup,scan,A
from pathlib import Path
from independent import build_frame
import numpy as np,pandas as pd,sys,json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import cv2
setup();root=Path(sys.argv[1]);public=Path(sys.argv[2]);scan.META=json.loads((Path(__file__).resolve().parent/'observations.json').read_text())
pred=dict(np.load(root/'terrain/cross-sun-centers.npz'))
records=json.loads((root/'terrain/cross-sun-links.json').read_text())
names=sorted(pred,key=lambda k:scan.META[k]['incidence_deg'])
columns=(len(names)+1)//2
fig,axes=plt.subplots(4,columns,figsize=(2*columns,8.8),layout='constrained')
for ax in axes.ravel():ax.set_axis_off()
rows=[]; cut={}
for j,k in enumerate(names):
 m=scan.META[k];p=pred[k];img=np.load(root/'tiles'/(k+'.npy'));a=cv2.getRectSubPix(img,(81,81),tuple(p.astype('f4')))
 cut[k]=a
 f=build_frame(k,root);gx,gy=p+np.array([2*scan.CORE-scan.PAD,11*scan.CORE-scan.PAD])
 sx,sy=f.native(gx,gy);lon,lat=scan.ORIGIN+np.array([gx,gy])*scan.GRID/scan.SCALE
 meta=records.get(k,{})
 rows.append(dict(product=k,incidence_deg=m['incidence_deg'],sample_zero=sx,line_zero=sy,corner_longitude=lon,corner_latitude=lat,terrain_link_cost=meta.get('cost',0)))
 for i,hw in enumerate([40,10]):
  ax=axes[i+2*(j//columns),j%columns];chip=a[40-hw:40+hw+1,40-hw:40+hw+1]
  q=np.percentile(chip,[2,99]);ax.imshow(chip,cmap='gray',vmin=q[0],vmax=q[1],interpolation="nearest")
  if i==0:ax.set_title(k+"\n"+str(m["incidence_deg"])+" deg",size=9);ax.plot([hw,hw],[hw-14,hw-6],color='c',lw=1);ax.plot([hw+6,hw+14],[hw,hw],color='c',lw=1)
  ax.axis('off')
pd.DataFrame(rows).to_csv(public/'native-locations.csv',index=False)
np.savez_compressed(public/'illumination-cutouts.npz',**cut)
fig.savefig(public/'illumination.png',dpi=125,bbox_inches='tight')
