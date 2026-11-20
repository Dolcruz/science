"""Compare candidate positions with published coordinate-bearing lunar catalog rows."""
from pathlib import Path
import pandas as pd
import numpy as np

here=Path(__file__).resolve().parent
positions=pd.read_csv(here/'comparison-positions.csv',dtype={'id':str})
sites=pd.read_csv(here/'sites.csv')
rows=[]
for site in sites.itertuples():
    for catalog,group in positions.groupby('catalog'):
        group=group.dropna(subset=['latitude','longitude_east']).copy()
        lat,lon=np.deg2rad(group.latitude),np.deg2rad(group.longitude_east)
        clat,clon=np.deg2rad([site.latitude,site.longitude_east])
        h=np.sin((lat-clat)/2)**2+np.cos(lat)*np.cos(clat)*np.sin((lon-clon)/2)**2
        group['distance_km']=3474.8*np.arcsin(np.sqrt(h.clip(0,1)))
        match=group.loc[group.distance_km.idxmin()].to_dict()
        rows.append(dict(site=site.site,coordinate_rows=len(group),**match))
pd.DataFrame(rows).to_csv(here/'nearest.csv',index=False)
