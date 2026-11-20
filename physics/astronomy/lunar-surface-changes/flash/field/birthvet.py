from search import *
from sharp import P,Q,T
from birth import sun

fld=ROOT/'birth'
df=pd.read_csv(fld/'records.csv')
def sm(a,s):return cv2.GaussianBlur(a,(0,0),s)
yy,xx=np.mgrid[-45:46,-45:46]
def local(pre,post):
    a=sm(np.log(np.maximum(100,pre)),.9);b=sm(np.log(np.maximum(100,post)),.9)
    ha=a-sm(a,8);hb=b-sm(b,8)
    mk=((np.hypot(xx,yy)>13)&(np.hypot(xx,yy)<31)).astype('u1')[12:-12,12:-12]
    cor=cv2.matchTemplate(ha,hb[12:-12,12:-12],cv2.TM_CCORR_NORMED,mask=mk)
    _,peak,_,(u,v)=cv2.minMaxLoc(cor)
    if min(u,v)<1 or max(u,v)>=24: return None
    def off(l,c,r):
        d=l-2*c+r
        return .5*(l-r)/d if d<0 else 0
    dx=u-12+off(cor[v,u-1],cor[v,u],cor[v,u+1]);dy=v-12+off(cor[v-1,u],cor[v,u],cor[v+1,u])
    a=cv2.warpAffine(a,np.float32([[1,0,-dx],[0,1,-dy]]),(91,91))
    return a,b,dx,dy,peak
def spot(a,sc,uv):
    bl=sm(a,.46*sc/.7)
    def move(q):
        du,dv=q*uv*sc/.7
        return cv2.warpAffine(bl,np.float32([[1,0,du],[0,1,dv]]),(91,91))
    return move(1),move(-1)
rows=[]
for _,s in df.iterrows():
    d=dict(np.load(fld/(s['name']+'.npz')))
    res=local(d[P],d[Q])
    if res is None:continue
    a,b,dx,dy,cc=res;pre=spot(a,s.sep,sun(P));post=spot(b,s.sep,sun(Q));diff=b-a;diff-=sm(diff,12)
    far,near=spot(diff,s.sep,sun(Q));ap=np.s_[43:48,43:48]
    old=cv2.dilate(pre[0]-pre[1],np.ones((5,5),'u1'))[ap]
    new=(post[0]-post[1])[ap]
    score=np.where((old<.40*new+.015)&(new>.10),np.minimum(far[ap],-near[ap]),-1)
    rows.append(dict(name=s['name'],aligned_score=score.max(),dx=dx,dy=dy,cc=cc))
z=df.merge(pd.DataFrame(rows),on='name').sort_values('aligned_score',ascending=False);z.to_csv(fld/'verified.csv',index=False)
print(z.head(24).to_string(index=False));print('remaining',sum(z.aligned_score>.025),'ranked',len(z))
