from sharp import *
from scipy.ndimage import maximum_filter
from shapely.geometry import Point
def gau(a,s):return cv2.GaussianBlur(a,(0,0),s)
def oriented(a,s,uv):
    smooth=gau(a,s*.46/.7)
    def get(q):
        m=np.float32([[1,0,q*uv[0]*s/.7],[0,1,q*uv[1]*s/.7]])
        return cv2.warpAffine(smooth,m,(scan.FULL,scan.FULL))
    return get(1),get(-1)
def sun(k):
    v=META[k];la,sl,dl=np.deg2rad([ORIGIN[1],v['sun_lat'],(v['sun_lon']-ORIGIN[0]+180)%360-180])
    e=np.sin(dl)*np.cos(sl);n=np.cos(la)*np.sin(sl)-np.sin(la)*np.cos(sl)*np.cos(dl)
    return np.array([e,-n])/np.hypot(e,n)
def run(table):
    scan.GRID=.7
    d=pd.read_csv(table)
    footprint=Polygon(((np.array(META[P]['corners'])-ORIGIN)*scan.SCALE)[[0,1,3,2]]).buffer(180)
    ds=d[[footprint.covers(Point(s.x,s.y)) for _,s in d.iterrows()]]
    coords=sorted(set(zip(np.floor(ds.x/(scan.CORE*.7)).astype(int),np.floor(ds.y/(scan.CORE*.7)).astype(int))))
    frames={k:frame(k,coords) for k in [P,Q,T,AFTER]}
    folder=ROOT/'birth';folder.mkdir(exist_ok=True);rows=[];area=[]
    for i,j in coords:
        ref=frames[AFTER].tile(i,j);des=scan.describe(ref);im={}
        for k in (P,Q,T):
            z=scan.align(frames[k].tile(i,j),ref,des)
            if z is not None:im[k]=z[0]
        if P not in im or Q not in im:continue
        pre=np.log(np.maximum(100,im[P]));post=np.log(np.maximum(100,im[Q]))
        d=post-pre;d-=gau(d,16/.7)
        valid=cv2.erode(np.uint8((im[P]>100)&(im[Q]>100)),np.ones((61,61),'u1')).astype(bool)
        inner=np.s_[scan.PAD:scan.PAD+scan.CORE,scan.PAD:scan.PAD+scan.CORE]
        layers=[]
        for sc in (1.2,2.1,3.5):
            a,b=oriented(pre,sc,sun(P));c,e=oriented(post,sc,sun(Q));u,v=oriented(d,sc,sun(Q))
            signal=np.minimum(u,-v)
            # A new sunlit far wall and shaded near wall, with small prior contrast at their positions.
            layers.append(np.where(valid&(c-e>.10)&(a-b<.40*(c-e)+.015),signal,0))
        score=np.max(layers,axis=0);ps=valid&(score>.032)&(score==maximum_filter(score,21))
        area.append((i,j,int(valid[inner].sum())))
        for yy,xx in np.argwhere(ps[inner]):
            x=xx+scan.PAD;y=yy+scan.PAD
            nm=f'x{i*scan.CORE+xx}y{j*scan.CORE+yy}'
            cs={k:a[y-45:y+46,x-45:x+46] for k,a in im.items() if a[y,x]>100}
            np.savez_compressed(folder/(nm+'.npz'),**cs)
            rows.append(dict(name=nm,east=.7*(i*scan.CORE+xx),south=.7*(j*scan.CORE+yy),score=score[y,x],sep=(1.2,2.1,3.5)[np.argmax([a[y,x] for a in layers])]))
        print(i,j,'spots',len(rows),'area',sum(a[2] for a in area)*.49/1e6,flush=True)
    pd.DataFrame(rows).sort_values('score',ascending=False).to_csv(folder/'records.csv',index=False)
    pd.DataFrame(area,columns=['i','j','pixels']).to_csv(folder/'area.csv',index=False)
if __name__=='__main__':run(candidate_input())
