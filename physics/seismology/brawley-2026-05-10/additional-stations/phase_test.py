"""Validate a Brawley waveform candidate on five stations unused for discovery."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,csv,json,hashlib
from xml.etree import ElementTree as ET
import numpy as np
from scipy.signal import butter,sosfiltfilt
from matplotlib import pyplot as plt
import requests
import pymseed

D=Path(__file__).resolve().parent
WAVE_URL='https://service.scedc.caltech.edu/fdsnws/dataselect/1/query'
PICK_URL='https://service.scedc.caltech.edu/fdsnws/event/1/query'
CANDIDATE='2026-05-10T03:30:01.960'
TEMPLATE='2026-05-10T03:16:47.510'
START='2026-05-10T03:12:00'
END='2026-05-10T03:34:00'
STATIONS={('SB','WLA'),('NP','5056'),('NP','5062'),('CI','CLI2'),('CI','COK2')}
def pos(s):return datetime.fromisoformat(s.rstrip('Z')).replace(tzinfo=timezone.utc).timestamp()
def read_trace(path):
    pieces=[]
    with pymseed.MS3TraceList.from_file(str(path),unpack_data=True) as records:
        for trace in records:
            for seg in trace:
                pieces.append((seg.starttime_seconds,seg.samprate,np.array(seg.datasamples,dtype=float)))
    rate=pieces[0][1]
    begin=pos(START)
    # Gaps outside the requested range can occur where the service trims records.
    z=np.full(round(rate*(pos(END)-begin)),np.nan)
    for at,sr,data in pieces:
        if sr!=rate:raise ValueError('Sampling rate changed')
        i=round((at-begin)*rate);lo=max(0,i);hi=min(len(z),i+len(data))
        if hi>lo:z[lo:hi]=data[lo-i:hi-i]
    edges=np.flatnonzero(np.diff(np.r_[False,np.isfinite(z),False]))
    filt=np.full_like(z,np.nan)
    sos=butter(4,(3,14),fs=rate,btype='bandpass',output='sos')
    for left,right in edges.reshape(-1,2):
        if right-left<=rate*4:continue
        filt[left:right]=sosfiltfilt(sos,z[left:right])
        filt[left:left+round(rate)]=np.nan
        filt[right-round(rate):right]=np.nan
    return filt,rate,begin
def correlation(a,b):
    a=a-a.mean();b=b-b.mean()
    return np.dot(a,b)/(np.linalg.norm(a)*np.linalg.norm(b))
def main(cache,out):
    cache.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True)
    xml=cache/'template.xml'
    if not xml.exists():
        r=requests.get(PICK_URL,params={'eventid':'41460424','includearrivals':'true'});r.raise_for_status();xml.write_bytes(r.content)
    records=[];curves=[];sources=[];cutouts={}
    for p in ET.parse(xml).findall('.//{*}pick'):
        w=p.find('{*}waveformID');n,s,l,c=(w.get(k,'') for k in ['networkCode','stationCode','locationCode','channelCode'])
        if (n,s) not in STATIONS:continue
        phase=p.findtext('{*}phaseHint');at=pos(p.findtext('{*}time/{*}value'))
        args=dict(net=n,sta=s,loc=l or '--',cha=c,starttime=START,endtime=END)
        ident='.'.join([n,s,l or '--',c]);f=cache/(ident+'.ms')
        url=requests.Request('GET',WAVE_URL,params=args).prepare().url
        if not f.exists():
            r=requests.get(url);r.raise_for_status()
            if not r.content:raise ValueError('Missing '+ident)
            f.write_bytes(r.content)
        sources.append(dict(channel=ident,url=url,sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
        z,sr,z0=read_trace(f)
        def cut(t,span=1.6,lead=.10):
            i=round((t-lead-z0)*sr)
            return z[i:i+round(span*sr)]
        ca=at+pos(CANDIDATE)-pos(TEMPLATE);a=cut(at);b=cut(ca)
        if not (np.isfinite(a).all() and np.isfinite(b).all()):
            print(ident,phase,"missing data in phase window",flush=True);continue
        fixed=correlation(a,b)
        # The controls and target are evaluated at the same prescribed lag.
        controls=np.arange(pos(START)+25,pos(END)-25,2.)
        controls=controls[(abs(controls-pos(TEMPLATE))>20)&(abs(controls-pos(CANDIDATE))>20)]
        cc=np.array([correlation(a,cut(t+at-pos(TEMPLATE))) for t in controls])
        cc=cc[np.isfinite(cc)]
        offsets=np.arange(-round(sr*.12),round(sr*.12)+1)/sr
        flex=np.array([correlation(a,cut(ca+i)) for i in offsets])
        long_a=cut(pos(TEMPLATE)+1,12,0);long_b=cut(pos(CANDIDATE)+1,12,0)
        bp=np.dot(a-a.mean(),b-b.mean())/np.dot(a-a.mean(),a-a.mean())
        records.append(dict(channel=ident,phase=phase,template_pick_utc=datetime.fromtimestamp(at,timezone.utc).isoformat(),rate=sr,
          prediction_utc=datetime.fromtimestamp(ca,timezone.utc).isoformat(),fixed_cc=fixed,symmetric_lag_s=offsets[flex.argmax()],lagged_cc=flex.max(),
          amplitude_ratio=bp,control_ge=int(sum(cc>=fixed)),control_count=len(cc),control_q99=np.percentile(cc,99),fixed_12s_cc=correlation(long_a,long_b)))
        curves.append((ident,phase,sr,a,b,fixed))
        cutouts[ident+'_'+phase]=np.stack((a,b,))
        print(ident,phase,'cc',round(fixed,3),'long',round(records[-1]['fixed_12s_cc'],3),'null',sum(cc>=fixed),len(cc),flush=True)
    np.savez_compressed(out/'phase-cutouts.npz',**cutouts)
    for name,items in [('phase-tests.csv',records),('sources.csv',sources)]:
        with (out/name).open('w',newline='',encoding='utf8') as f:
            writer=csv.DictWriter(f,fieldnames=items[0]);writer.writeheader();writer.writerows(items)
    fig,axes=plt.subplots(len(curves),1,figsize=(9,1.02*len(curves)),sharex=True,layout='constrained')
    for ax,(ident,phase,sr,a,b,cc) in zip(axes,curves):
        xx=np.arange(len(a))/sr-.1
        for sig,col,lab in [(a,'#78919d','Cataloged reference'),(b,'#b53d20','Candidate')]:
            ax.plot(xx,(sig-sig.mean())/sig.std(),color=col,lw=1,label=lab)
        ax.axvline(0,color='k',lw=.6,ls=':');ax.set_yticks([]);ax.set_ylabel(ident+'  '+phase,rotation=0,ha='right',va='center',fontsize=8)
        ax.text(.99,.80,f'r = {cc:.2f}',transform=ax.transAxes,ha='right',fontsize=8)
    axes[0].legend(frameon=False,ncol=2,loc='lower center',bbox_to_anchor=(.5,1.09))
    axes[-1].set_xlabel('Seconds from the predicted phase arrival')
    fig.savefig(out/'five-station-phases.png',dpi=155);plt.close(fig)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('cache',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();main(a.cache,a.output)
