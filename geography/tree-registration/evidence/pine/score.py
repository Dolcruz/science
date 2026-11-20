"""Score a row-aligned prediction for the S5 pair small_pine_anim_42_0_2."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


REFERENCE = Path(__file__).with_name("reference.npz")
REFERENCE_SHA256 = "03cce23b7be72dd2fd52b27baacffe616494beae70abc76f038fe44e82acb8c7"

# Each source hash covers every coordinate in row-major, little-endian order.
LAYOUTS = {
    (174614, 8): ("full_rows", "c437a892a38f77e0a365a7b1e3e05ad1e5c74d66d4cad31eed7a51d85a191191"),
    (179070, 4): ("published_rows", "363e0867dfd6a9b8c08b437d35d622c0859cbdacf7f53cdd20d22016cb9aacd2"),
}


def score(path):
    with REFERENCE.open("rb") as stream:
        if hashlib.sha256(stream.read()).hexdigest() != REFERENCE_SHA256:
            raise ValueError("Reference archive checksum mismatch")
        stream.seek(0)
        with np.load(stream, allow_pickle=False) as ref, np.load(path, allow_pickle=False) as pred:
            xyz = pred["s_pc"]
            if (xyz.ndim != 2 or xyz.shape[1] != 3 or xyz.dtype.kind != "f"
                    or (len(xyz), xyz.dtype.itemsize) not in LAYOUTS):
                raise ValueError("Source shape or precision does not match either published pine layout")
            layout, digest = LAYOUTS[len(xyz), xyz.dtype.itemsize]
            coords = np.ascontiguousarray(xyz, dtype=xyz.dtype.newbyteorder("<"))
            if hashlib.sha256(coords).hexdigest() != digest:
                raise ValueError("Source coordinates or row order differ from the verified pine scan")
            motion = pred["s2t_flow"]
            if motion.shape != xyz.shape or motion.dtype.kind != "f" or motion.dtype.itemsize != 4:
                raise ValueError("Expected one float32 3D displacement per source row")
            if not np.isfinite(motion).all():
                raise ValueError("Displacement field contains a nonfinite component")
            delta = motion[ref[layout]] - ref["reference_flow_m"]
    # Same float32 endpoint distances and sum as the archive, then divide in double precision.
    error_m = np.sqrt(np.sum(delta * delta, axis=1, dtype=np.float32) + np.float32(1e-20))
    return error_m, layout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prediction", type=Path, help="Combined CLI output or published MV *_out.npz")
    parser.add_argument("--point-errors", type=Path, metavar="FILE.npy",
                        help="Also save each endpoint error in metres in reference order to a new file")
    args = parser.parse_args()
    try:
        errors, layout = score(args.prediction)
        if args.point_errors:
            with args.point_errors.open("xb") as out:
                np.save(out, errors, allow_pickle=False)
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, f"Cannot score prediction: {exc}\n")
    mean_m = float(errors.sum(dtype=np.float32)) / len(errors)
    print(json.dumps({"pair": "small_pine_anim_42_0_2", "source_layout": layout,
                      "points": len(errors), "mean_epe_m": mean_m, "mean_epe_cm": mean_m * 100,
                      "points_over_10_cm": int(np.count_nonzero(errors > .10))}, indent=2))


if __name__ == "__main__":
    main()
