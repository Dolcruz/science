import json
from pathlib import Path
import numpy as np,pandas as pd, rasterio
from rasterio.windows import from_bounds
from scipy import ndimage as ndi
from matplotlib import pyplot as plt
import certifi
from matplotlib.colors import ListedColormap
p=Path(__file__).resolve().parent
tiles=['04WFD','05WNU','03WWP','03WXU']
def band(meta,name,extent,size):
    cache=p/'spectra';cache.mkdir(exist_ok=True)
    key=cache/f"{meta['id']}_{name}_{int(extent[0])}_{int(extent[1])}_{size}.npy"
    if key.is_file():return np.load(key)
    a=meta['assets'][name]
    with rasterio.open(a['href']) as d:
        w=from_bounds(*extent,transform=d.transform)
        arr=d.read(1,window=w,out_shape=(size,size),resampling=rasterio.enums.Resampling.nearest).astype('float32')
        nodata=arr==0
        b=a['raster:bands'][0];arr=(arr*b['scale']+b.get('offset',0));arr[nodata]=np.nan
    np.save(key,arr);return arr
def run():
 fig,axs=plt.subplots(len(tiles),4,figsize=(11,2.9*len(tiles)),layout='constrained')
 for axrow,tile in zip(axs,tiles):
    f=pd.read_csv(p/(tile+'-candidates.csv')).iloc[0];pre=int(f.year)-2024
    arr=np.load(p/(tile+'-water.npz'))['water'][pre];layer,n=ndi.label(arr,structure=np.ones((3,3)))
    m=layer==int(f.label);sel=np.nonzero(m);minr,maxr=sel[0].min(),sel[0].max();minc,maxc=sel[1].min(),sel[1].max()
    scenes=json.loads((p/(tile+'-pick.json')).read_text())
    x0=scenes[0]['assets']['scl']['proj:transform'][2];y0=scenes[0]['assets']['scl']['proj:transform'][5]
    size=(max(maxr-minr+1,maxc-minc+1)+18)*6;ec=x0+((minc+maxc+1)/2)*60;nc=y0-((minr+maxr+1)/2)*60
    extent=(ec-size*5,nc-size*5,ec+size*5,nc+size*5)
    for year,ax in zip(range(2023,2027),axrow):
        eligible=[]
        for a in scenes:
            if not a['date'].startswith(str(year)):continue
            with rasterio.open(p/'scl'/(a['id']+'.tif')) as dd:
                s=dd.read(1,window=from_bounds(*extent,transform=dd.transform))
            ok=np.isin(s,[4,5,6]).mean();eligible.append((ok,a['date'],a))
        ok,_,a=max(eligible,key=lambda row:(row[0],-row[-1]['cloud']))
        g,nir,sw=[band(a,k,extent,size) for k in ['green','nir','swir16']]
        rgb=np.stack((sw/.24,nir/.34,g/.18),axis=-1)
        ax.imshow(np.nan_to_num(np.clip(rgb,0,1)));ax.axis('off')
        ax.set_title(f"{a['date']}   {tile}\n{100*ok:.0f}% usable",fontsize=8)
        print(tile,a['date'],size,ok,flush=True)
 fig.savefig(p/'basins.png',dpi=100)
if __name__=='__main__':
 with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR',CURL_CA_BUNDLE=certifi.where()):run()
