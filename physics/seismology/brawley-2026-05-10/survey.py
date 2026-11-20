"""Network waveform matching for the 10 May 2026 Brawley swarm."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
from pathlib import Path
from urllib.request import urlopen

import numpy as np
from scipy import signal

HERE = Path(__file__).resolve().parent
DISCOVERY = ('IMP', 'SWS', 'SNR')
RANKING = ('DRE', 'RXH', 'ELO')
STATIONS = DISCOVERY + RANKING
MIDNIGHT = datetime(2026, 5, 10, tzinfo=timezone.utc).timestamp()
START, END = 7200, 14400
RATE = 50
TEMPLATE, CANDIDATE = 11807.51, 12601.96
TEMPLATE_MAGNITUDE = 1.96
FILTER = signal.butter(4, [2, 12], fs=100, btype='bandpass', output='sos')


def iso(seconds):
    return datetime.fromtimestamp(MIDNIGHT + seconds, timezone.utc).strftime('%H:%M:%S.%f')[:-3]


def write_table(path, rows):
    with path.open('w', newline='', encoding='utf8') as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0], lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def download(path, source):
    if not path.exists():
        with urlopen(source['url']) as stream:
            path.write_bytes(stream.read())
    if hashlib.sha256(path.read_bytes()).hexdigest() != source['sha256']:
        raise ValueError(f'Unexpected SHA-256 for {path.name}')


def native(path, begin, end):
    """Count samples on their native 100 Hz clock, preserving gap checks."""
    import pymseed
    count = round((end - begin) * 100)
    samples = np.empty(count, dtype=np.int32)
    valid = np.zeros(count, dtype=bool)
    with pymseed.MS3TraceList.from_file(str(path), unpack_data=True) as traces:
        for trace in traces:
            for segment in trace:
                if segment.samprate != 100:
                    raise ValueError(f'Unexpected sample rate in {path.name}')
                i = round((segment.starttime_seconds - MIDNIGHT - begin) * 100)
                a, b = max(0, i), min(count, i + segment.numsamples)
                if a < b:
                    samples[a:b] = np.asarray(segment.datasamples)[a-i:b-i]
                    valid[a:b] = True
    if not np.all(valid):
        raise ValueError(f'Waveform gap in analysis interval for {path.name}')
    return samples


def correlations(data, snippet):
    t = snippet.astype('f8')
    t -= t.mean()
    n = len(t)
    squared = np.r_[0, np.cumsum(data.astype('f8')**2)]
    total = np.r_[0, np.cumsum(data, dtype='f8')]
    variance = squared[n:] - squared[:-n] - (total[n:] - total[:-n])**2/n
    denominator = np.sqrt(np.maximum(variance, 1e-9)) * np.linalg.norm(t)
    return signal.oaconvolve(data, t[::-1].astype('f4'), mode='valid') / denominator


def replay(cache, out):
    cache.mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)
    sources = list(csv.DictReader((HERE / 'waveform-sources.csv').open()))
    band, chips = {}, {}
    for source in sources:
        sta, channel = source['station'], source['channel']
        path = cache/source['filename']
        download(path, source)
        if channel == 'HHZ':
            whole = native(path, START-30, END+40)
            band[sta] = signal.sosfiltfilt(FILTER, whole)[3000::2].astype('f4')
        for key, origin in [('reference', TEMPLATE), ('candidate', CANDIDATE)]:
            chips[f'{key}_{sta}_{channel}'] = native(path, origin-30, origin+40)
    np.savez_compressed(out/'native-cutouts.npz', **chips)

    catalog = list(csv.DictReader((HERE/'search-origins.csv').open()))
    templates = [r for r in catalog if r['use_template'] == 'True']
    catalog_times = np.array([float(r['seconds_utc']) for r in catalog])
    size = (END-START)*RATE
    best = np.full(size, -1, dtype='f4')
    which = np.zeros(size, dtype=int)
    peaks_by_template = {}

    def cc(station, origin):
        v = band[station]
        k = round((origin + 1 - START)*RATE)
        return correlations(v, v[k:k+12*RATE])[RATE:RATE+size]

    for j, r in enumerate(templates):
        origin = float(r['seconds_utc'])
        z = np.mean([cc(sta, origin) for sta in DISCOVERY], axis=0)
        update = z > best
        best[update], which[update] = z[update], j
    peaks = signal.find_peaks(best, distance=6*RATE, height=.25)[0]
    for i in peaks:
        origin = START + i/RATE
        if np.min(np.abs(catalog_times-origin)) >= 15:
            peaks_by_template.setdefault(which[i], []).append(i)

    # One-second circular shifts keep the three ranking stations together. Each
    # shift re-ranks the entire list of search peaks against their own templates.
    shift = np.arange(END-START)*RATE
    null = np.full(len(shift), -1.)
    records = []
    for j, indices in peaks_by_template.items():
        r = templates[j]
        origin = float(r['seconds_utc'])
        curves = [cc(sta, origin) for sta in RANKING]
        for i in indices:
            sample = START + i/RATE
            z = np.median(np.stack([v[(i+shift)%size] for v in curves]), axis=0)
            null = np.maximum(null, z)
            records.append(dict(utc=iso(sample), seconds_utc=sample, template_id=r['id'],
                                discovery_mean=float(best[i]), ranking_median=z[0],
                                nearest_search_origin_s=np.min(abs(catalog_times-sample))))
    records.sort(key=lambda r: r['ranking_median'], reverse=True)
    write_table(out/'search-peaks.csv', records)
    write_table(out/'time-shifts.csv', [dict(shift_seconds=i, maximum_ranking_median=v)
                                        for i,v in enumerate(null)])
    print(f'{len(templates)} templates, {len(peaks)} peaks, {len(records)} outside catalog windows')
    print(records[0])
    print(f'{sum(null[1:] >= null[0])} of {len(null)-1} shifted maxima reach observed maximum')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, default=Path('data'))
    parser.add_argument('--output', type=Path, default=Path('results'))
    args = parser.parse_args()
    replay(args.cache, args.output)
