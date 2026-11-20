"""Plot compatible illumination pairs and produce local measurements."""
from field import *
from coordinates import SITES
def produce():
    d=np.load(D/'registered.npz');e=np.load(D/'opposing-relief.npz')
    pairs=[('2010 east',high(d['pre10']),high(d['postH'])-high(d['postA'])),('2019 west',high(e['pre_west']),high(e['post_west'])-high(d['postA'])),('2018 moderate',high(d['pre18']),high(d['postM'])-high(d['postA']))]
    keys=[("2018-02-20  ·  49°",d['pre18']),("2010-12-09  ·  71°",d['pre10']),("2019-03-22  ·  80°",e['pre_west']),
          ("2025-12-25  ·  38°",d['postM']),("2026-01-22  ·  69°",d['postH']),("2026-07-30  ·  83°",e['post_west'])]
    evidence=[];ties=[]
    for site,(x,y) in SITES.items():
        fig,axs=plt.subplots(2,3,figsize=(9.4,6.4),layout='constrained')
        w=18;extent=[-w-.5,w+.5,w+.5,-w-.5]
        for i,(ax,(name,img)) in enumerate(zip(axs.flat,keys)):
            a=img[y-w:y+w+1,x-w:x+w+1]
            ax.imshow(a,cmap='gray',interpolation='nearest',vmin=np.percentile(a,1),vmax=np.percentile(a,99),extent=extent)
            ax.set_title(name,fontsize=10)
            ax.plot([0,0],[-7,-4.5],color='#36dbb0',lw=1.2);ax.plot([-7,-4.5],[0,0],color='#36dbb0',lw=1.2)
            ax.set_xticks([-10,0,10]);ax.set_yticks([-10,0,10]);ax.tick_params(labelsize=8)
            if i<3:ax.set_xlabel(['Moderate Sun','East Sun','West Sun'][i],fontsize=9)
            if i==0:ax.set_ylabel("Before the impact",fontsize=10)
            if i==3:ax.set_ylabel("After the impact",fontsize=10)
        lon,lat=forward_map(x,y)
        title={'NW':'Northwestern candidate depression','NNE':'Northern tongue and older crater rim','old_pit_control':'Nearby pre-existing crater control'}[site]
        fig.suptitle(f'{title}\n{lat:.5f}° N, {lon:.5f}° E  ·  offsets in metres  ·  north up',fontsize=14)
        fig.savefig(D/f'sequence-{site}.png',dpi=160);plt.close(fig)
        gap=2 if site=='NW' else 3
        for key,img in keys+[('2026-07-17 east',e['post_east']),('2025-11-28 high Sun',d['postA'])]:
            l=img[y-1:y+2,x-gap-1:x-gap+2].mean();r=img[y-1:y+2,x+gap-1:x+gap+2].mean()
            evidence.append(dict(site=site,x=x,y=y,epoch=key,left_right_log_ratio=float(np.log(l/r)),center_separation_m=2*gap))
        for key,a,b in pairs:
            off=[]
            for v in range(-120,121,30):
                for u in range(-120,121,30):
                    if np.hypot(u,v)<45:continue
                    xx=x+u;yy=y+v;l=15;h=20
                    arr=a[yy-h-l:yy+h+l+1,xx-h-l:xx+h+l+1];ref=b[yy-h:yy+h+1,xx-h:xx+h+1]
                    if ref.shape!=(41,41) or arr.shape!=(71,71):continue
                    corr=cv2.matchTemplate(arr,ref,cv2.TM_CCOEFF_NORMED);j,i=np.unravel_index(corr.argmax(),corr.shape)
                    if corr[j,i]>=.55 and max(abs(i-l),abs(j-l))<l:off.append([i-l,j-l,corr[j,i]])
            t=np.asarray(off)
            ties.append(dict(site=site,pair=key,count=len(t),median_dx=float(np.median(t[:,0])),median_dy=float(np.median(t[:,1])),median_corr=float(np.median(t[:,2])),q75_offset_m=float(np.percentile(np.hypot(t[:,0],t[:,1]),75))))
    pd.DataFrame(evidence).to_csv(D/'lobe-contrasts.csv',index=False)
    pd.DataFrame(ties).to_csv(D/'local-registration.csv',index=False)
    fig,axes=plt.subplots(1,2,figsize=(10.2,4.1),layout='constrained')
    for ax,(site,(sx,sy)) in zip(axes,list(SITES.items())[:2]):
        distance=np.arange(-16,17)
        vals=d['dtm'][sy-1:sy+2,sx-16:sx+17].mean(axis=0)
        baseline=np.linspace(vals[0],vals[-1],len(vals));ax.plot(distance,vals-baseline,color='#555b61',label='Published 3 m DTM',lw=2)
        stereo=np.load(D/'stereo-apertures.npz')
        for method,colour in [('EN','#c26925'),('NW','#536eb7'),('EW','#27846c')]:
            a=stereo[site+'_'+method];c=a.shape[1]//2
            temp=a[c-1:c+2,c-16:c+17];v=np.full(len(distance),np.nan)
            for j in range(len(v)):
                if np.isfinite(temp[:,j]).any():v[j]=np.nanmedian(temp[:,j])
            far=(abs(distance)>10)&np.isfinite(v)
            coeff=np.polyfit(distance[far],v[far],1)
            ax.plot(distance,v-np.polyval(coeff,distance),'.-',color=colour,label={'EN':'East–nadir','NW':'Nadir–west','EW':'East–west'}[method],lw=1,ms=3)
        ax.axhline(0,color='.7',lw=.6);ax.axvline(0,color='.7',lw=.6)
        ax.set_title({'NW':'Northwestern site','NNE':'Northern site'}[site]);ax.set_xlabel('East offset (m)');ax.set_ylabel('Relative relief (m)');ax.legend(fontsize=8)
    fig.savefig(D/'stereo-profiles.png',dpi=160);plt.close(fig)
    fig,ax=plt.subplots(figsize=(7,6.4),layout='constrained')
    a=d['postA'];ax.imshow(a,cmap='gray',vmin=np.percentile(a,1),vmax=np.percentile(a,97),extent=[-600,600,-600,600])
    for r in [160,585]:ax.add_patch(plt.Circle((0,0),r,fill=False,color='white',ls='--',lw=.8))
    for site,(x,y) in list(SITES.items())[:2]:
        dx,dy=x-600,600-y;ax.plot(dx,dy,'o',mec='#f77d39',mfc='none',ms=10,mew=1.8);ax.annotate(site,(dx,dy),xytext=(8,9),textcoords='offset points',color='#ffbe77',weight='bold')
    ax.set_xlabel('East of McGetchin (m)');ax.set_ylabel('North of McGetchin (m)');ax.set_title('Search annulus and candidate sites')
    fig.savefig(D/'field-locations.png',dpi=150);plt.close(fig)
if __name__=="__main__":
    with threadpool_limits(limits=4):produce()
