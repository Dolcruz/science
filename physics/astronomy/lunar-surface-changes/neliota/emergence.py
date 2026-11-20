"""Order registered detections by emergence of compact relief on previously quiet terrain."""
from pathlib import Path
import sys
import pandas as pd,numpy as np,cv2
from threadpoolctl import threadpool_limits
from review import sheet

def morphology(a,b):
    y,x=np.indices(a.shape)-32;r=np.hypot(x,y);mask=r<=5.5; bg=(r>=9)&(r<20)
    def strength(img):
        log=np.log(np.maximum(img,100))
        fine=cv2.GaussianBlur(log,(0,0),1.1)
        h=fine-cv2.GaussianBlur(fine,(0,0),7)
        center=h[mask]-np.median(h[bg]);return np.percentile(abs(center),85), np.percentile(center,[10,90])
    old,old_range=strength(a);new,new_range=strength(b)
    return old,new,new/(old+.015),*(new_range-old_range)

def main(p):
    f=pd.read_csv(p/'ranked.csv')
    with np.load(p/'cutouts.npz') as z:
        vals=[morphology(*z[k]) for k in f.chip]
        f[['pre_structure','post_structure','emergence','trough_change','peak_change']]=vals
        # Search for morphology that became appreciable over initially quiet ground.
        f['passes']=(f.pre_structure<.06)&(f.post_structure>=.055)&(f.emergence>=1.6)&(f.local_score>=3)
        f.sort_values(['passes','emergence'],ascending=False).to_csv(p/'emergence.csv',index=False)
        hits=f[f.passes].sort_values('emergence',ascending=False)
        for i in range(0,len(hits),40):sheet(hits.iloc[i:i+40],z,p/f'emergent-{i//40+1:02d}.jpg')
        print('eligible',len(hits),'of',len(f),flush=True)
if __name__=='__main__':
    cv2.setNumThreads(4)
    with threadpool_limits(4,'blas'):main(Path(sys.argv[1]))
