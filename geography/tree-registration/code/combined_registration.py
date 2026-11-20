"""Register observed tree geometry with WindReg96 and robust local motion refinement."""

import argparse
from hashlib import sha256
from importlib.util import find_spec
import json
from pathlib import Path
from zipfile import ZipFile

import numpy as np
from branch_motion import register as refine

ROOT = Path(__file__).resolve().parent
WHEEL = "windreg-0.1.0-py3-none-any.whl"
WHEEL_SHA256 = "eb63a904ea7d0f0bde48ad2967a6b55a07b2c8fed9b9ea41b7065a61777290d7"


def windreg96():
    """Require the installed implementation and trained parameters from the bundled wheel."""
    wheel = ROOT / WHEEL
    if sha256(wheel.read_bytes()).hexdigest() != WHEEL_SHA256:
        raise ValueError("Bundled WindReg96 wheel differs from the qualified release")
    spec = find_spec("windreg")
    if spec is None or spec.origin is None:
        raise ImportError("Install the bundled wheel and its dependencies with pip install -r requirements.txt")
    directory = Path(spec.origin).resolve().parent
    with ZipFile(wheel) as archive:
        for name in archive.namelist():
            if name.startswith("windreg/") and not name.endswith("/"):
                path = directory / name.removeprefix("windreg/")
                if not path.is_file() or path.read_bytes() != archive.read(name):
                    raise ImportError(f"Installed WindReg differs at {name}. Install the bundled wheel in a fresh environment.")
    from windreg import scan_motion
    if Path(scan_motion.__file__).resolve() != directory / "scan_motion.py":
        raise ImportError("WindReg96 import path differs from the verified installation")
    return scan_motion


def run(source_file, anchor_file, original_file, output, up):
    if output.suffix.lower() != ".npz":
        raise ValueError("Use a new .npz path for the prediction")
    if output.exists():
        raise FileExistsError(f"Output already exists: {output}")
    up = np.asarray(up, dtype=np.float64)
    if up.shape != (3,) or not np.isfinite(up).all() or not np.any(up):
        raise ValueError("Physical up must be a finite nonzero direction in scan coordinates")
    model = windreg96()
    spacing = json.loads((ROOT / "settings.json").read_text(encoding="utf8"))["spacing_m"]
    source = np.load(source_file, allow_pickle=False, mmap_mode="r")
    with np.load(anchor_file, allow_pickle=False) as data:
        anchors = {k: data[k] for k in ("source", "target", "confidence")}
    with np.load(original_file, allow_pickle=False) as data:
        original_source, target, original_flow = (data[k] for k in ("s_pc", "t_pc", "s2t_flow"))
    if any(a.dtype.kind not in "fiu" for a in (source, original_source, target, original_flow, *anchors.values())):
        raise ValueError("Coordinates, confidences and displacements must be real numeric arrays")
    initial, _ = model.register(source, target, anchors, original_source, original_flow, model.load_models(), up=up)
    flow = refine(source, initial=initial, spacing=spacing)
    with output.open("xb") as stream:
        try:
            np.savez(stream, s_pc=source, t_pc=target, s2t_flow=flow)
        except BaseException:
            stream.close()
            output.unlink()
            raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="NPY containing the observed full source union, in metres")
    parser.add_argument("anchors", type=Path, help="Predicted matches NPZ with source, target and confidence")
    parser.add_argument("original_prediction", type=Path, help="Original predicted_motion NPZ with s_pc, t_pc and s2t_flow")
    parser.add_argument("output", type=Path, help="New row-aligned predicted-motion NPZ")
    parser.add_argument("--up", nargs=3, type=float, required=True, metavar=("X", "Y", "Z"),
                        help="Measured physical up direction in the scan frame")
    args = parser.parse_args()
    try:
        run(args.source, args.anchors, args.original_prediction, args.output, args.up)
    except (OSError, ValueError, KeyError, ImportError) as e:
        parser.exit(1, f"Unable to register scans: {e}\n")
    print(f"Saved {args.output}")
