"""Run the CPU deformation estimator with predicted point correspondences."""
import argparse
import numpy as np
from elastic_field import register

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("observed", "matches", "output"):
        parser.add_argument(name)
    args = parser.parse_args()
    with np.load(args.observed, allow_pickle=False) as scans:
        source, target = scans["source"], scans["target"]
    with np.load(args.matches, allow_pickle=False) as matches:
        anchors = {k: matches[k] for k in ("source", "target", "confidence")}
    flow = register(source, target, anchors)
    with open(args.output, "xb") as stream:
        np.savez(stream, s_pc=source, t_pc=target, s2t_flow=flow)
