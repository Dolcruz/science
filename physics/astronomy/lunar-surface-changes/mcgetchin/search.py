"""Find repeatable crater-oriented shading absent from the two pre-impact frames."""
from field import *
from scipy.spatial import cKDTree

def grad_score(arr,s,unit):
    gy,gx=np.gradient(blur(arr,s))
    return s*(gx*unit[0]+gy*unit[1])

def peaks():
    z=np.load(D/"registered.npz"); l=json.loads((D/"registration.json").read_text())["brightness_gradient_directions"]
    a={k:high(z[k]) for k in NAMES if k!="dtm"}
    # Subtract high-Sun albedo structure from the two lower-Sun post exposures.
    # Flat-field scatter is evaluated over contiguous lunar terrain beyond the primary ejecta.
    highpost=a["postH"]-a["postA"];medpost=a["postM"]-a["postA"]
    h10=a["pre10"];m18=a["pre18"]
    topo=z["dtm"]; dist=np.hypot(X-600,Y-600)
    records=[]
    annulus=(dist>280)&(dist<585)
    for s in (1.,1.5,2.25,3.5,5.,7.5,11.):
        unit=np.float32(l["postH"])
        fields=[grad_score(arr,s,np.float32(l[name])) for arr,name in [
            (highpost,"postH"),(medpost,"postM"),(h10,"pre10"),(m18,"pre18")]]
        ps,ms,bs,cs=fields
        # Fit relative responses using reliable old pits outside the changed blanket.
        old=(dist>430)&(dist<570)&(bs>np.percentile(bs[annulus],92))&(cs>np.percentile(cs[annulus],85))
        scale_b=np.median(ps[old]/bs[old]);scale_c=np.median(ps[old]/cs[old]);scale_m=np.median(ps[old]/np.maximum(ms[old],.001))
        # Tiny local shifts must not convert the flank of an old pit into a new one.
        radius=max(3,int(np.ceil(.8*s)))
        kernel=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*radius+1,2*radius+1))
        pre=np.maximum(cv2.dilate(bs,kernel)*scale_b,cv2.dilate(cs,kernel)*scale_c)
        post=np.minimum(ps,ms*scale_m)
        change=post-np.maximum(0,pre)
        # Rank by residual relative to the spatial scatter on outer terrain.
        null=change[(dist>440)&(dist<570)]
        med=np.median(null);sd=1.4826*np.median(abs(null-med))
        score=(change-med)/max(.001,sd)
        depth=blur(topo,2.1*s)-blur(topo,.6*s)
        support=(dist>160)&(dist<585)
        k=2*int(np.ceil(2.2*s))+1
        mask=(score==cv2.dilate(score,np.ones((k,k),'u1')))&support&(score>=4)&(post>.012)
        for cy,cx in zip(*np.where(mask)):
            records.append(dict(x=int(cx),y=int(cy),radius_m=float(dist[cy,cx]),sigma=s,score=float(score[cy,cx]),change=float(change[cy,cx]),post=float(post[cy,cx]),pre=float(pre[cy,cx]),dtm_depth=float(depth[cy,cx])))
        print(s,round(scale_b,2),round(scale_c,2),round(scale_m,2),round(sd,3),int(mask.sum()))
    tab=pd.DataFrame(records).sort_values("score",ascending=False);tab.to_csv(D/"all-peaks.csv",index=False)
    # A single depression generally activates more than one filter width.
    coords=tab[["x","y"]].to_numpy();tree=cKDTree(coords);seen=set();selected=[]
    for i,t in enumerate(tab.itertuples()):
        if i in seen:continue
        selected.append(i);seen.update(tree.query_ball_point(coords[i],max(8,3*t.sigma)))
    tab.iloc[selected].to_csv(D/"distinct.csv",index=False)

def sheet(rows,filename,window=22):
    d=np.load(D/"registered.npz")
    names=["pre10","pre18","postH","postM","postA","dtm"]
    sheets=[]
    for row in rows.itertuples():
        cy,cx=int(row.y),int(row.x); sl=np.s_[cy-window:cy+window+1,cx-window:cx+window+1]
        fig,axs=plt.subplots(1,len(names),figsize=(12,2.3))
        for ax,name in zip(axs,names):
            a=d[name][sl].copy()
            if name=="dtm":
                yy,xx=np.indices(a.shape);v=np.c_[xx.ravel(),yy.ravel(),np.ones(a.size)];coef=np.linalg.lstsq(v,a.ravel(),rcond=None)[0]; a=a-(v@coef).reshape(a.shape)
            ax.imshow(a,cmap='gray' if name!="dtm" else 'viridis',vmin=np.percentile(a,1),vmax=np.percentile(a,99),interpolation='nearest')
            ax.set_title(name,fontsize=9);ax.set_xticks([]);ax.set_yticks([])
            ax.plot([window,window],[window-12,window-7],color='#2ce7cf',lw=1)
        axs[0].set_ylabel(f"({cx},{cy})\nR={row.radius_m:.0f} m\ns={row.sigma:g} z={row.score:.1f}",fontsize=8)
        fig.tight_layout(); fig.canvas.draw(); frame=np.asarray(fig.canvas.buffer_rgba())[:,:,:3].copy();plt.close(fig);sheets.append(frame)
    img=np.concatenate(sheets,axis=0);Image.fromarray(img).save(D/filename)

if __name__=="__main__":
    with threadpool_limits(limits=4):
        peaks(); t=pd.read_csv(D/"distinct.csv")
        for label,group in [("outside",t.query("radius_m>=280")),("inner",t.query("radius_m<280")),("depth",t.query("dtm_depth>.20 and radius_m>=230"))]:
            if len(group):
                sheet(group.head(18),label+".jpg")
