"""Test complementary-Sun relief signatures in three pre/post image pairs."""
from field import *
import opposite

def hl(a):
    h=np.log(np.maximum(a,10));return h-blur(h,16)
def pair(a,b):
    """Fit and remove a smoothly varying local amplitude ratio in the outer field."""
    aa=np.sqrt(np.maximum(.0004,blur(blur(a,1.5)**2,45)))
    bb=np.sqrt(np.maximum(.0004,blur(blur(b,1.5)**2,45)))
    return a/aa,b/bb

def profile(slope,s):
    sm=blur(slope,s)
    width=max(2,int(round(1.5*s)))
    left=np.roll(sm,width,axis=1);right=np.roll(sm,-width,axis=1)
    bg=blur(sm,5*s+3)
    return np.minimum(bg-left,right-bg)
def search():
    d=np.load(D/"registered.npz");ext=np.load(D/"additional.npz")
    wpre,west,east,sun=[ext[k] for k in opposite.IDS]
    def mosaic(main,other):
        # Prefer the middle of each detector wherever their coverage overlaps.
        mask=lambda a: cv2.morphologyEx((a>0).astype('u1'),cv2.MORPH_CLOSE,np.ones((21,21),'u1'))
        a=cv2.distanceTransform(mask(main),cv2.DIST_L2,3)
        b=cv2.distanceTransform(mask(other),cv2.DIST_L2,3)
        return np.where(a>=b,main,other)
    if opposite.COMPANIONS[0] in ext:east=mosaic(east,ext[opposite.COMPANIONS[0]])
    if opposite.COMPANIONS[1] in ext:west=mosaic(west,ext[opposite.COMPANIONS[1]])
    # Refine similar-illumination ties for each epoch against well-registered terrain.
    wpre,_=reg(wpre,west,1); east,_=reg(east,d["postH"],1);sun,_=reg(sun,d["pre18"],1)
    preE=high(d["pre10"]);preW=hl(wpre)
    postE=hl(east);postW=hl(west)
    # Remove stationary albedo using the independent near-noon image in each epoch.
    aspre=hl(sun);aspost=high(d["postA"])
    e0,w0=pair(preE-aspre,preW-aspre);e1,w1=pair(postE-aspost,postW-aspost)
    s0=(w0-e0)*.5;s1=(w1-e1)*.5
    # Minimum support for all four grazing-Sun exposures and both albedo images.
    footprint=lambda a:cv2.morphologyEx((a>0).astype("u1"),cv2.MORPH_CLOSE,np.ones((21,21),"u1")).astype(bool)
    cov=footprint(wpre)&footprint(west)&footprint(east)&footprint(sun)
    cov=cv2.erode(cov.astype("u1"),np.ones((51,51),"u1")).astype(bool)
    field=cov&(R>160)&(R<585)
    saved={k:v for k,v in zip(("pre_west","post_west","post_east","pre_albedo"),(wpre,west,east,sun))}
    np.savez_compressed(D/"opposing-relief.npz",s0=s0,s1=s1,coverage=field,**saved)
    cands=pd.read_csv(D/"distinct.csv");seed=[]
    surveyed=[]
    for s in (1.,1.5,2.25,3.5,5.,7.5,11.):
        a,b=profile(s0,s),profile(s1,s)
        k=2*max(3,int(np.ceil(.8*s)))+1
        pre=cv2.dilate(a,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(k,k)))
        delta=b-np.maximum(0,pre)
        cal=cov&(R>440)&(R<570)
        med=np.median(delta[cal]);sd=1.4826*np.median(abs(delta[cal]-med))
        z=(delta-med)/sd
        for row in cands.loc[cands.sigma==s].itertuples():
            x,y=row.x,row.y;win=np.s_[y-2:y+3,x-2:x+3]
            i,j=np.unravel_index(np.argmax(z[win]),(5,5));u=x+j-2;v=y+i-2
            seed.append(dict(x=x,y=y,sigma=s,covered=bool(field[y,x]),relief_z=float(z[v,u]),relief=float(b[v,u]),pre=float(pre[v,u]),centroid_x=u,centroid_y=v))
        n=2*max(3,round(2*s))+1
        use=(z==cv2.dilate(z,np.ones((n,n),'u1')))&(z>3)&(b>.25)&field
        for y,x in zip(*np.where(use)):
            surveyed.append(dict(x=int(x),y=int(y),sigma=s,z=float(z[y,x]),after=float(b[y,x]),prior=float(pre[y,x]),radius_m=float(R[y,x])))
    t=pd.DataFrame(surveyed).sort_values('z',ascending=False);t.to_csv(D/'opposite-extrema.csv',index=False)
    keep=[];covered=set();pp=t[['x','y']].to_numpy();tree=cKDTree(pp)
    for i,row in enumerate(t.itertuples()):
        if i in covered:continue
        keep.append(i);covered.update(tree.query_ball_point(pp[i],max(8,3*row.sigma)))
    t.iloc[keep].to_csv(D/'opposite-distinct.csv',index=False)
    q=cands.merge(pd.DataFrame(seed),on=['x','y','sigma'],suffixes=('_discovery','_opposing'))
    q.to_csv(D/'replication.csv',index=False)
    print("area km2",field.sum()/1e6,"seed covered",q.covered.sum(),"top")
    print(q[q.covered].nlargest(12,'relief_z')[['x','y','radius_m','score','relief_z','relief','dtm_depth']].round(3).to_string(index=False))
    print("full",len(t),len(keep),t.head(6).round(3).to_string(index=False))

def panel(rows,name,win=16):
    d=np.load(D/"registered.npz");e=np.load(D/"opposing-relief.npz")
    keys=[("2010 / east",d['pre10']),("2019 / west",e['pre_west']),("2018",d['pre18']),("2025",d['postM']),("Jan26 / east",d['postH']),("Jul26 / east",e['post_east']),("Jul26 / west",e['post_west']),("before slopes",e['s0']),("after slopes",e['s1'])]
    result=[]
    for x,y in rows:
        sl=np.s_[y-win:y+win+1,x-win:x+win+1];fig,axs=plt.subplots(1,len(keys),figsize=(14,2.0))
        for ax,(key,a) in zip(axs,keys):
            v=a[sl];lo,hi=np.percentile(v,[1,99])
            ax.imshow(v,cmap="gray" if 'slopes' not in key else "RdBu_r",vmin=lo if 'slopes' not in key else -2,vmax=hi if 'slopes' not in key else 2,interpolation="nearest");ax.set_xticks([]);ax.set_yticks([]);ax.set_title(key,fontsize=8);ax.plot([win,win],[win-10,win-5],color="#1ae6b4",lw=1)
        axs[0].set_ylabel(f"({x}, {y})",fontsize=8);fig.tight_layout();fig.canvas.draw();result.append(np.asarray(fig.canvas.buffer_rgba())[:,:,:3].copy());plt.close(fig)
    if result:Image.fromarray(np.concatenate(result,axis=0)).save(D/name)
if __name__=="__main__":
    with threadpool_limits(limits=4):
        search()
        t=pd.read_csv(D/'replication.csv').query('covered').nlargest(15,'relief_z')
        panel(list(zip(t.x,t.y)),"opposite-replication.jpg")
        t=pd.read_csv(D/'opposite-distinct.csv').head(16)
        panel(list(zip(t.x,t.y)),"opposite-search.jpg")
