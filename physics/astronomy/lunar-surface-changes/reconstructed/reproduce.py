"""Reproduce the N13-field survey and image measurements from public planetary data."""
import argparse
from pathlib import Path
import os
import subprocess
import sys

HERE=Path(__file__).resolve().parent
B="M186762974RC"
A="M1148028911RC"
FIRST=[A,"M1193942227LC","M1117402542LC","M1446530029RC","M1191587829LC","M1176284678RC","M1168044929RC","M1229246404RC","M1109154536RC","M178510938LC","M1185701417RC","M1526159508RC","M1186879028LC"]
SECOND=[A,"M1193942227LC","M1117402542LC","M1446530029RC","M1191587829LC","M1176284678RC","M1526159508RC","M178510938LC","M1185701417RC","M1109154536RC","M1186879028LC","M1168044929RC","M1229246404RC","M1209240188LC",B]
def call(name,*args):
    subprocess.run([sys.executable,str(HERE/(name+'.py')),*map(str,args)],check=True)
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("folder",type=Path)
    args=p.parse_args()
    for k in ["OPENBLAS_NUM_THREADS","OMP_NUM_THREADS","MKL_NUM_THREADS"]:os.environ[k]="4"
    os.environ["PYTHONDONTWRITEBYTECODE"]="1"
    raw=args.folder.resolve();out=raw/'results';out.mkdir(exist_ok=True,parents=True)
    call("fetch",raw)
    call("survey",raw,raw/'survey')
    call("inspect_peaks",raw,raw/'survey',out/'atlas')
    call("independent",raw,HERE/'observations.json',out,2432,10103,B,"M1117402542LC","M1193942227LC","M1191587829LC","M1209240188LC","M1446530029RC","M1168044929RC","M1229246404RC","M178510938LC","M1185701417RC","M1526159508RC")
    call("photometry",out/'site-2432-10103.npz',out)
    call("tiles",raw)
    call("terrain",raw/'tiles',raw/'terrain',*FIRST)
    call("terrain",raw/'tiles',raw/'terrain',"--resume",*SECOND)
    call("cross_sun",raw/'tiles',raw/'terrain')
    call("illumination",raw,out)
    call("grazing",raw,out)
    call("kaguya",raw,out)
