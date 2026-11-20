from independent import setup,scan,build_frame,A,B
from pathlib import Path
import json
import numpy as np
import sys
setup();d=Path(sys.argv[1]);out=d/'tiles';out.mkdir(exist_ok=True)
scan.META=json.loads((Path(__file__).resolve().parent/'observations.json').read_text())
for n in scan.META:
 if not(out/(n+'.npy')).exists():
  arr=build_frame(n,d).tile(2,11);np.save(out/(n+'.npy'),arr);print(n,flush=True)
