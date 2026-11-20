"""Extract the dated SCSN origins and special Brawley relocations for waveform matching."""
import argparse
from pathlib import Path
from urllib.request import urlopen
from survey import START, END, write_table

ANNUAL = 'https://scedc-pds.s3.amazonaws.com/earthquake_catalogs/SCEC_DC/2026.catalog'
RELOCATED = 'https://service.scedc.caltech.edu/ftp/catalogs/SCSN_DD/Brawley_hypodd_cat'


def extract(annual, relocated):
    rows = []
    for line in annual.splitlines():
        if not line.startswith('2026/05/10'):
            continue
        _, time, _, _, mag, _, lat, lon, depth, _, event, *_ = line.split()
        h, m, s = map(float, time.split(':'))
        sec = h*3600+m*60+s
        use = (START+10 < sec < END-20 and 1.2 <= float(mag) <= 3.1
               and abs(float(lat)-32.965) < .065 and abs(float(lon)+115.556) < .065)
        rows.append(dict(catalog='SCSN', id=event, seconds_utc=sec, latitude=lat,
                         longitude=lon, depth_km=depth, magnitude=mag, use_template=use))
    for line in relocated.splitlines():
        f = line.split()
        if f[10:13] == ['2026','5','10']:
            sec = int(f[13])*3600+int(f[14])*60+float(f[15])
            rows.append(dict(catalog='Brawley DD', id=f[0], seconds_utc=sec, latitude=f[1],
                             longitude=f[2], depth_km=f[3], magnitude=f[16], use_template=False))
    return rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    with urlopen(ANNUAL) as a, urlopen(RELOCATED) as r:
        write_table(args.output, extract(a.read().decode(), r.read().decode()))
