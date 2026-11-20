from pathlib import Path
import re,sys,csv,json
from itertools import product
import requests,numpy as np,pandas as pd
from shapely import wkt
from shapely.geometry import box
from math import sin,cos,atan2,radians,degrees

here=Path(__file__).resolve().parent
def flashes():
    raw=(here/'paper.txt').read_text(encoding='utf-8').replace('−','-')
    t1=raw.split('Table A.1: Photometric results')[1].split('Table A.2: Results')[0]
    t2=raw.split('Table A.2: Results')[1].split('Table A.3:')[0]
    vals={}
    for m in re.finditer(r'(\d{3})[a-z]?\s+(\d{4})\s+(\d\d)\s+(\d\d)\s+\d\d:\d\d:[\d.]+\s+Val\.\s+\d+\s+[\d.]+\(\d+\)\s+[\d.]+\(\d+\)\s+(-?[\d.]+)\s+(-?[\d.]+)',t1):
        k,y,mo,d,lat,lon=m.groups()
        vals[int(k)]=dict(id=int(k),date=f'{y}-{mo}-{d}',lat=float(lat),lon=float(lon)%360)
    for row in t2.splitlines():
        a=row.split()
        if len(a)==17 and a[0].isdigit() and int(a[0]) in vals and '(' in a[12]:
            vals[int(a[0])]['diam_m']=float(a[12].split('(')[0])
    return pd.DataFrame(vals.values()).dropna().sort_values('diam_m',ascending=False)

def observations(r):
    dest=here/f'ode-all-{int(r.id)}.json'
    if not dest.exists():
        endpoint='https://oderest.rsl.wustl.edu/live2/'
        par=dict(query='product',target='moon',ihid='LRO',iid='LROC',pt='CDRNAC4',westernlon=r.lon-.5,easternlon=r.lon+.5,minlat=r.lat-.5,maxlat=r.lat+.5,output='json')
        count=int(requests.get(endpoint,params={**par,'results':'c'}).json()['ODEResults']['Count'])
        resp=requests.get(endpoint,params={**par,'results':'m','limit':count})
        resp.raise_for_status()
        q=resp.json()['ODEResults']
        if q.get('Status','').lower()!='success':raise RuntimeError(q)
        if len(q['Products']['Product'])!=count:raise ValueError('Incomplete product list')
        dest.write_text(json.dumps(q))
    q=json.loads(dest.read_text())
    arr=q.get('Products',{}).get('Product',[]) if q.get('Products') else []
    obs={}
    for row in arr:
        if float(row['Map_resolution'])>1.5 or float(row['Emission_angle'])>18 or not 25<=float(row['Incidence_angle'])<=78:continue
        note=next((x for x in row['ODE_notes']['ODE_note'] if 'LROLRC' in x),None)
        n=row['Product_name'].split('.')[0]
        if note:
            v=next(csv.reader([note]))
            corners=[[float(v[i+1]),float(v[i])] for i in [77,71,75,73]]
            slat,slon=float(v[63]),float(v[64])
            lines,samples=int(v[52]),int(v[53])
        else:
            html=here/(n+'.html')
            if not html.exists():
                resp=requests.get(row['External_url']);resp.raise_for_status();html.write_text(resp.text,encoding='utf-8')
            fields=dict(re.findall(r'<td>([^<>]+)</th>\s*<td>([^<>]+)</td>',html.read_text(encoding='utf-8')))
            corners=[[float(fields[k+' longitude']),float(fields[k+' latitude'])] for k in ['Upper left','Upper right','Lower left','Lower right']]
            slat,slon=float(fields['Sub solar latitude']),float(fields['Sub solar longitude'])
            lines,samples=int(fields['Image lines']),int(fields['Line samples'])
        lat,lon,slat,slon=map(radians,[r.lat,r.lon,slat,slon])
        bearing=degrees(atan2(sin(slon-lon)*cos(slat),cos(lat)*sin(slat)-sin(lat)*cos(slat)*cos(slon-lon)))%360
        obs[n]=dict(date=row['Observation_time'][:10],incidence_deg=float(row['Incidence_angle']),emission=float(row['Emission_angle']),subsolar_lat=degrees(slat),subsolar_lon=degrees(slon),bearing=bearing,res=float(row['Map_resolution']),original=row['LabelURL'][:-4]+'.IMG',corners=corners,lines=lines,samples=samples,poly=row['Footprint_geometry'])
    return obs

def pairs(r,obs):
    # Compare only similar local solar directions and nadir-like sharp observations.
    region=box(r.lon-.5,r.lat-.5,r.lon+.5,r.lat+.5)
    sharp={n:m for n,m in obs.items() if m['res']<=1.5 and m['emission']<=18 and 25<=m['incidence_deg']<=78}
    before=[(n,m) for n,m in sharp.items() if m['date']<r.date]
    after=[(n,m) for n,m in sharp.items() if m['date']>r.date]
    rows=[]
    for (a,m),(b,v) in product(before,after):
        di=abs(m['incidence_deg']-v['incidence_deg'])
        ds=abs((m['bearing']-v['bearing']+180)%360-180)
        worst=max(m['res'],v['res'])
        if di>6 or ds>7:continue
        land=wkt.loads(m['poly']).intersection(wkt.loads(v['poly'])).intersection(region)
        area=land.area*30.323**2*cos(radians(r.lat))
        if area<=0:continue
        rows.append(dict(id=r.id,diam_m=r.diam_m,before=a,after=b,di=di,ds=ds,area=area,res=worst,score=area*r.diam_m**2/worst**2/(1+di/2+ds/3)))
    return rows

if __name__=='__main__':
    f=flashes();f.to_csv(here/'flashes.csv',index=False);print(f.head(14).to_string(index=False),flush=True)
    out=[]
    for r in f.itertuples():
        if r.diam_m<4:continue
        obs=observations(r)
        rows=pairs(r,obs);out.extend(rows)
        print(r.id,len(obs),len(rows),max((z['score'] for z in rows),default=0),flush=True)
        pd.DataFrame(out).sort_values('score',ascending=False).to_csv(here/'pairs.csv',index=False) if out else None
