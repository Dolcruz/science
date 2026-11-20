"""Second review: ground eclipse timing and depths with the eclipse window re-centred.

Run from the entry folder:  python review/centred_window.py
Uses measure.py's own time conversion and phase function. Writes review/centred-depths.csv.
"""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import numpy as np, pandas as pd
import measure as M

P, E = 2.70917244, 4293.6915795
g = pd.read_csv(HERE / "bochum-curves.csv")
g["btjd"] = M.bochum_btjd(g.mjd_utc.to_numpy())

# TESS folded profile (sectors with apertures on TIC 349414709) as the eclipse template
t = np.load(HERE / "tess-curves.npz")
ph_t = np.concatenate([M.phase(t[f"time{s}"], P, E) for s in (7, 34, 61, 88)])
fl_t = np.concatenate([t[f"flux{s}"] for s in (7, 34, 61, 88)])
edges = np.arange(-.05, .0501, .002); cen = edges[:-1] + .001
prof = np.array([np.median(fl_t[(ph_t >= a) & (ph_t < a + .002)]) for a in edges[:-1]])

h = g[g.source == "TIC 349414709"].copy()
h["phase"] = M.phase(h.btjd, P, E)
h["cycle"] = np.rint((h.btjd - E) / P)

def chi2(q, base, sh, sc):
    f = np.interp(q.phase - sh, cen, prof, left=1, right=1)
    m = -2.5 * np.log10(1 - (1 - f) * sc)
    return np.sum(((q.mag - base - m) / q.mag_err) ** 2)

print("Ground eclipse centre relative to the TESS-only ephemeris (both bands combined):")
for era, sel in [("2011-2013", h.cycle < -1700), ("2017-2018", h.cycle > -1400), ("all", h.cycle < 0)]:
    tot = {}
    for b in "ri":
        hb = h[h.band == b]
        base = hb[(abs(hb.phase) > .035) & (abs(hb.phase) < .43)].mag.median()
        q = hb[sel[hb.index] & (abs(hb.phase) < .06)]
        for sh in np.arange(-.03, .0301, .0005):
            tot[sh] = tot.get(sh, 0) + min(chi2(q, base, sh, sc) for sc in np.arange(.8, 1.31, .05))
    best = min(tot, key=tot.get)
    one = [s for s in tot if tot[s] < tot[best] + 1]
    zero = tot[min(tot, key=abs)]
    print(f"  {era}: {best*P*1440:+.1f} min (1 sigma {min(one)*P*1440:+.1f} to {max(one)*P*1440:+.1f}),"
          f" delta chi2 of zero shift = {zero - tot[best]:.1f}")

rng = np.random.default_rng(1)
rows = []
for shift_min in (0.0, -39.0):
    ph = M.phase(g.btjd - shift_min / 1440.0, P, E)
    for src in ("TIC 349414709", "TIC 349414705", "TIC 349414726"):
        for b in "ri":
            m = (g.source == src) & (g.band == b)
            inn = g[m & (np.abs(ph) < .018)].mag.to_numpy()
            base = g[m & (np.abs(ph) > .035) & (np.abs(ph) < .43)].mag.to_numpy()
            loss = 1 - 10 ** (-0.4 * (np.median(inn) - np.median(base)))
            bs = [1 - 10 ** (-0.4 * (np.median(rng.choice(inn, len(inn))) - np.median(rng.choice(base, len(base)))))
                  for _ in range(2000)]
            rows.append(dict(centre_shift_min=shift_min, source=src, band=b, n_in_eclipse=len(inn),
                             flux_loss_pct=round(100 * loss, 2), bootstrap_sd_pct=round(100 * np.std(bs), 2)))
out = pd.DataFrame(rows)
out.to_csv(HERE / "review" / "centred-depths.csv", index=False)
print(out.to_string(index=False))
