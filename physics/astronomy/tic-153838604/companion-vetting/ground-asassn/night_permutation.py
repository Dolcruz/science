"""Exact matched-night tests of ASAS-SN dimming against zero and two TESS profiles.

For each sharp null, first remove its multiplicative attenuation from each
actual event. Assign the attenuations to every possible choice of one night per
stratum. For each assignment, refit its baseline and noise weight with that
night held out. Positive statistics mean deeper dimming than the sharp null.
Exchangeability of matched nights and independence of strata are assumptions.
"""
import csv
from itertools import product
import sys

import numpy as np
import pandas as pd
from astropy import constants as constants, units as units
from astropy.coordinates import get_body_barycentric
from astropy.time import Time

from analyze import HERE, HALF, TARGET, offsets

sys.path.insert(0, str(HERE.parent))
from eclipse_models import NODES, WEIGHTS, loss


def target_data():
    table = pd.read_parquet(HERE / "lightcurve.parquet")
    data = table[(table.quality == "G") & (table.flux > 0)].copy()
    utc = Time(data.jd.to_numpy(), format="jd", scale="utc")
    light_time = (TARGET.cartesian.xyz.value @ get_body_barycentric("earth", utc).xyz / constants.c)
    data["t"] = utc.tdb.jd + light_time.to_value(units.day)
    return data


def matched_nights(data):
    distance = offsets(data.t, 0.)
    events = data[abs(distance) < HALF].sort_values("jd")
    strata = []
    for event in events.itertuples():
        dt = data.t - event.t
        good = ((data.camera == event.camera) & (abs(dt) > .5) & (abs(dt) <= 30.)
                & (abs(distance) > .08) & (abs(offsets(data.t, .5)) > .08))
        controls = data[good].groupby(np.floor(dt[good]+.5)).flux.median().to_numpy()
        if len(controls) == 0:
            raise ValueError(f"No matched control nights for JD {event.jd}")
        strata.append((float(offsets(event.t, 0.)), np.r_[event.flux, controls]))
    return strata


def event_loss(model, times):
    if model is None:
        return np.zeros(len(times))
    # Use the same contiguous 270-second coadd approximation as compare_bands.py.
    sample = np.asarray(times)[:,None] + (270. / 86400 / 2.) * NODES
    return loss(sample, model.impact, model.speed_Rstar_day, model.k,
                model.assumed_flux_ratio, (model.u1, model.u2)) @ WEIGHTS


def possible_scores(nights, attenuation, shape):
    unobscured = nights.copy()
    unobscured[0] /= 1. - attenuation
    choices = []
    for j, target in enumerate(unobscured):
        others = np.delete(unobscured, j)
        base = np.median(others)
        controls = 1000. * (1. - others / base)
        sigma = 1.4826 * np.median(abs(controls - np.median(controls)))
        if not np.isfinite(sigma) or sigma <= 0:
            raise ArithmeticError("Indeterminate leave-one-out noise scale")
        observed = 1000. * (1. - (1.-attenuation) * target / base)
        predicted = 1000. * attenuation
        weight = shape / sigma**2
        choices.append((weight*(observed-predicted), weight*shape, weight*predicted))
    return choices


def test(calibration, strata, model):
    times = [t for t,_ in strata]
    losses = event_loss(model, times)
    groups = [possible_scores(nights, ell, 1.-abs(t)/HALF)
              for (t,nights),ell in zip(strata,losses)]
    # When all indices are zero, all assignments coincide with the actual dates.
    actual = np.sum([g[0] for g in groups], axis=0)
    excess = actual[0] / actual[1]
    prediction = actual[2] / actual[1]
    greater = absolute = total = 0
    for assignment in product(*groups):
        numerator, denominator, _ = np.sum(assignment, axis=0)
        statistic = numerator / denominator
        greater += int(statistic >= excess)
        absolute += int(abs(statistic) >= abs(excess))
        total += 1
    return dict(calibration=calibration, null="zero loss" if model is None else model.example,
                events=len(groups), control_nights=" ".join(str(len(x)-1) for x in groups),
                predicted_depth_ppt=prediction, measured_depth_ppt=prediction+excess,
                excess_depth_ppt=excess, assignments=total, deeper_or_equal=greater,
                one_sided_tail=greater/total, abs_equal_or_larger=absolute,
                two_sided_abs_tail=absolute/total)


def main():
    models = pd.read_csv(HERE.parent/"eclipse_models.csv")
    selected = models[(models.u1 == .35) & models.example.isin(["1.20 RJ","0.15 solar radii"])]
    assert len(selected) == 2
    rows = []
    for label,data in [("target only",target_data()),
                       ("inner comparison field",pd.read_csv(HERE/"calibrated-target.csv")),
                       ("outer comparison field",pd.read_csv(HERE/"outer-field"/"calibrated-target.csv"))]:
        strata = matched_nights(data)
        for m in [None,*selected.itertuples()]:
            rows.append(test(label,strata,m))
    with (HERE/"permutation.csv").open("w",newline="",encoding="utf-8") as out:
        writer = csv.DictWriter(out,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(pd.DataFrame(rows).to_string(index=False))


if __name__ == "__main__":
    main()
