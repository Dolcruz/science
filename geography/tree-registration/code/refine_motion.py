"""Refine a predicted displacement field on a tree point cloud."""

import argparse
import json
from pathlib import Path

import numpy as np
from branch_motion import register


def refine(source, flow):
    """Return float32 displacements, in metres, aligned to the source rows."""
    if any(np.asarray(a).dtype.kind not in "fiu" for a in (source, flow)):
        raise ValueError("Source coordinates and displacements must be real numeric arrays")
    config = json.loads(Path(__file__).with_name("settings.json").read_text(encoding="utf-8"))
    return register(source, initial=flow, spacing=config["spacing_m"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--paper", type=Path, help="Published *_out.npz prediction with s_pc and s2t_flow arrays")
    inputs.add_argument("--source", type=Path, help="Source coordinates as an (N, 3) .npy array, in metres")
    parser.add_argument("--flow", type=Path, help="Predicted displacements matching --source row for row, in metres")
    parser.add_argument("output", type=Path, help="New .npy file for refined displacements")
    args = parser.parse_args()
    if (args.source is None) != (args.flow is None):
        parser.error("--source and --flow must be supplied together")
    if args.output.suffix.lower() != ".npy":
        parser.error("Output must have a .npy extension")
    if args.output.exists():
        parser.error(f"Output already exists: {args.output}")
    try:
        if args.paper is not None:
            with np.load(args.paper, allow_pickle=False) as archive:
                source, flow = archive["s_pc"], archive["s2t_flow"]
        else:
            if any(path.suffix.lower() != ".npy" for path in (args.source, args.flow)):
                parser.error("Separate input files must have a .npy extension")
            source, flow = (np.load(path, allow_pickle=False, mmap_mode="r") for path in (args.source, args.flow))
        result = refine(source, flow)
        with args.output.open("xb") as stream:
            try:
                np.save(stream, result, allow_pickle=False)
            except BaseException:
                stream.close()
                args.output.unlink()
                raise
    except (OSError, ValueError, TypeError, KeyError) as e:
        parser.exit(1, f"Unable to refine motion: {e}\n")
    print(f"Saved {len(result):,} displacements to {args.output}")


if __name__ == "__main__":
    main()
