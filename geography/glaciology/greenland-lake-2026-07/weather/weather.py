"""Extract PROMICE hourly in-situ meteorology around the western Greenland lake event."""
from pathlib import Path
from datetime import datetime,timezone
import csv,json,hashlib,re
import requests
import numpy as np
import pandas as pd
from pyproj import Geod

OUT=Path(__file__).resolve().parent
BASE='https://thredds.geus.dk/thredds/dodsC/aws/l3sites/netcdf/hour/KAN_M_hour.nc'
def ascii_fields(names,stride):
    url=BASE+'.ascii?'+','.join(name+stride for name in names)
    response=requests.get(url);response.raise_for_status()
    data=response.text.split('---------------------------------------------')[-1]
    arrays={name:np.fromstring(vals,sep=',') for name,vals in re.findall(r'(?m)^(\w+)\[\d+\]\s*\n([^\n]+)',data)}
    if set(arrays)!=set(names):raise ValueError(data[:300])
    return arrays,url
def main():
    desc=requests.get(BASE+'.das');desc.raise_for_status()
    units=re.search(r'\btime \{\s+String units "hours since ([^"]+)',desc.text).group(1)
    base_dt=pd.Timestamp(units,tz='UTC')
    # Derive indices from server coordinates; the time axis need not be contiguous.
    tt,_=ascii_fields(['time'],'')
    start=pd.Timestamp('2026-07-16',tz='UTC');end=pd.Timestamp('2026-07-28',tz='UTC')
    lo=np.searchsorted(tt['time'],(start-base_dt).total_seconds()/3600)
    hi=np.searchsorted(tt['time'],(end-base_dt).total_seconds()/3600)
    fields=['time','t_u','t_surf','dsr_cor','usr_cor','dlr','ulr','gps_lat','gps_lon','gps_alt','wspd_u']
    arrays,url=ascii_fields(fields,f'[{lo}:1:{hi-1}]')
    df=pd.DataFrame(arrays);df['time']=base_dt+pd.to_timedelta(df.time,unit='h');df.set_index('time',inplace=True)
    df.to_csv(OUT/'KAN_M-hourly.csv',index_label='time_utc')
    print('first/last',df.index.min(),df.index.max(),'available',df.notna().sum().to_dict())
    print(df[['t_u','t_surf','dsr_cor','gps_lat','gps_lon','gps_alt']].resample('D').mean().round(2))
    src={'source':BASE+'.html','subset':url,'units':units,'time_interpretation':'UTC hourly time coordinate','fields':{}}
    for field in fields[1:]:
        info=re.search(r'\b'+field+r' \{([^}]+)',desc.text).group(1)
        src['fields'][field]={k:v for k,v in re.findall(r'String (units|long_name) "([^"]*)"',info)}
    (OUT/'source.json').write_text(json.dumps(src,indent=2))
    part=df.loc['2026-07-22 10:00':'2026-07-23 14:00']
    print('bracket',len(part),part.t_u.describe().to_dict(),'above zero',(part.t_u>0).sum(),'station coordinates',part[['gps_lat','gps_lon','gps_alt']].median().to_dict())
    rad=part.dsr_cor-part.usr_cor+part.dlr-part.ulr
    dist=Geod(ellps='WGS84').inv(part.gps_lon.median(),part.gps_lat.median(),-48.53845,67.12718)[2]/1000
    summary=dict(station='KAN_M',distance_km=dist,hourly_air_temperatures=len(part),
                 min_c=part.t_u.min(),max_c=part.t_u.max(),mean_c=part.t_u.mean(),
                 positive_hours=int((part.t_u>0).sum()),net_radiation_mean_w_m2=rad.mean(),
                 net_radiation_values=int(rad.count()))
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(summary)
if __name__=='__main__':main()
