"""What the ASAS-SN estimator would read for an exactly achromatic eclipse."""
import numpy as np
import pandas as pd
from batman import _quadratic_ld

from analyze import HERE


def main():
    models = pd.read_csv(HERE.parent/"eclipse_models.csv")
    models = models[(models.u1==.35)&models.example.isin(["1.20 RJ","0.15 solar radii"])]
    results = []
    for name,path in [("target only",HERE/"phase-0-measurements.csv"),
                      ("inner comparison field",HERE/"differential-0-events.csv"),
                      ("outer comparison field",HERE/"outer-field/differential-0-events.csv")]:
        d=pd.read_csv(path)
        w=d.profile/d.control_mad_ppt**2
        w=w/sum(w*d.profile)
        t=d.offset_hours.to_numpy()[:,None]/24
        nodes,weights=np.polynomial.legendre.leggauss(12)
        # Low-cadence survey epochs usually combine three 90-second exposures.
        tt=t+nodes*270/(2*86400)
        for model in models.itertuples():
            z=np.hypot(model.impact,model.speed_Rstar_day*tt).ravel()
            losses=(1-_quadratic_ld._quadratic_ld(z,model.k,model.u1,model.u2,1)).reshape(tt.shape)
            predicted = (losses @ (weights/2))*1000/(1+model.assumed_flux_ratio)
            results.append(dict(calibration=name,example=model.example,achromatic_depth_estimate_ppt=w@predicted,
                                measured_depth_estimate_ppt=w@d.deficit_ppt))
    pd.DataFrame(results).to_csv(HERE/"achromatic-predictions.csv",index=False)
    print(pd.DataFrame(results).round(3).to_string(index=False))


if __name__=="__main__":
    main()
