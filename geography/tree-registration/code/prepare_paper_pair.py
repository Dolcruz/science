"""Prepare WindReg96 inputs from one released S5 test pair and its observed patches."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import numpy as np


HERE = Path(__file__).resolve().parent
KEYS = ("source", "target", "confidence")
CONFIG_LF_SHA256 = {
    "lepard.yaml": "6b5894d42432113c3893bf2555ca4561a684b81343cf2a1462dbda9eed20a665",
    "outlier_rejection.yaml": "a93f31760a2636adfeabb60567a22801119283117b88d490d5acddd290476383",
}


def file_hash(path):
    result = sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            result.update(chunk)
    return result.hexdigest()


def patch_signature(patches):
    return sha256("".join(f"{name}\t{value}\n" for name, value in patches).encode()).hexdigest()


def load_matcher(repo, weights, inventory):
    from tree_match import AuthorMatcher

    model = inventory["matcher"]
    if file_hash(HERE / "tree_match.py") != model["source_sha256"]:
        raise ValueError("Unexpected MV matcher integration")
    for name, expected in model["weights_sha256"].items():
        if file_hash(weights / name) != expected:
            raise ValueError("Unexpected MV checkpoint: " + name)
    for name, expected in CONFIG_LF_SHA256.items():
        content = (repo / "correspondence/configs" / name).read_bytes()
        if sha256(content.replace(b"\r\n", b"\n")).hexdigest() != expected:
            raise ValueError("Unexpected S5 correspondence configuration: " + name)
    return AuthorMatcher(repo, weights, model["neighborhood_limits"], "cuda")


def prepare(test_root, original, destination, cache=None, repo=None, weights=None):
    if destination.exists():
        raise FileExistsError("Choose a new output directory: " + str(destination))
    if not original.name.endswith("_out.npz"):
        raise ValueError("Use a released MV file with a name ending in _out.npz")
    if (repo is None) != (weights is None) or (cache is None) == (repo is None):
        raise ValueError("Choose either the S5 match cache or both the author repository and S5 weights")
    inventory_file = HERE / "s5_pair_inputs.json"
    inventory = json.loads(inventory_file.read_text(encoding="utf-8"))
    pair = original.name.removesuffix("_out.npz")
    entry = inventory["pairs"].get(pair)
    if entry is None or file_hash(original) != entry["published_mv_sha256"]:
        raise ValueError("This file is outside the 97 released MV-Tree-LNDP S5 predictions")
    tree = pair.rsplit("_", 2)[0]
    paths = sorted((test_root / tree).glob(pair + "_c*.npz"))
    if len(paths) != entry["patches"]:
        raise ValueError(f"Expected {entry['patches']} regular source patches in {test_root / tree}")
    if patch_signature((p.stem, file_hash(p)) for p in paths) != entry["patch_file_list_sha256"]:
        raise ValueError("Regular patch data or patch order differ from the released S5 pair")
    matcher = load_matcher(repo, weights, inventory) if cache is None else None
    source_parts = []
    matches = {key: [] for key in KEYS}
    for path in paths:
        with np.load(path, allow_pickle=False) as data:
            source = np.asarray(data["s_pc"], dtype=np.float64)
            if matcher is not None:
                predicted, _ = matcher.predict(source, data["t_pc"])
                for key in KEYS:
                    matches[key].append(predicted[key])
            source_parts.append(source)
    points = np.concatenate(source_parts)
    del source_parts
    keys = np.ascontiguousarray(points, dtype=np.float32).view(np.dtype((np.void, 12))).ravel()
    source = points[np.unique(keys, return_index=True)[1]]
    del keys, points
    destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=destination.parent) as tmp:
        result = Path(tmp) / "inputs"
        result.mkdir()
        np.save(result / "source.npy", source, allow_pickle=False)
        if len(source) != entry["regular_source_rows"] or file_hash(result / "source.npy") != entry["source_npy_sha256"]:
            raise ValueError("Assembled source rows differ from the verified S5 row order")
        anchor_path = result / "anchors.npz"
        if cache is not None:
            with ZipFile(cache) as zipped:
                payload = zipped.read(f"anchors/{pair}.npz")
            if sha256(payload).hexdigest() != entry["anchors_npz_sha256"]:
                raise ValueError("S5 correspondence cache does not match this pair")
            anchor_path.write_bytes(payload)
        else:
            np.savez(anchor_path, **{key: np.concatenate(parts) for key, parts in matches.items()})
        with np.load(anchor_path, allow_pickle=False) as data:
            a, b, p = (data[key] for key in KEYS)
        if (a.ndim != 2 or a.shape[1] != 3 or a.shape != b.shape or p.shape != (len(a),)
                or any(not np.isfinite(x).all() for x in (a, b, p)) or np.any((p < 0) | (p > 1))):
            raise ValueError("Invalid predicted correspondences")
        info = {"pair": pair, "regular_patches": len(paths), "source_points": len(source),
                "matches": len(p), "matches_above_0.2": int((p > .2).sum()),
                "matcher": "cached" if cache is not None else "fresh author networks",
                "source_sha256": entry["source_npy_sha256"], "anchors_sha256": file_hash(anchor_path),
                "original_sha256": entry["published_mv_sha256"], "input_inventory_sha256": file_hash(inventory_file),
                "patch_file_list_sha256": entry["patch_file_list_sha256"], "weights_sha256": inventory["matcher"]["weights_sha256"]}
        (result / "provenance.json").write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
        result.rename(destination)
    return info


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("test_root", type=Path, help="S5_patches/test directory with per-tree subdirectories")
    parser.add_argument("original", type=Path, help="Merged MV-Tree-LNDP predicted_motion/*_out.npz")
    parser.add_argument("destination", type=Path, help="New directory for source.npy, anchors.npz and provenance")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--cache", type=Path, help="Companion s5_predicted_matches.zip")
    group.add_argument("--author-repo", type=Path, help="Prepared, checked-out author DeformationPyramid tree")
    parser.add_argument("--weights", type=Path, help="Directory containing the two S5 stems checkpoints")
    args = parser.parse_args()
    if bool(args.author_repo) != bool(args.weights):
        parser.error("--weights is used with --author-repo")
    print(json.dumps(prepare(args.test_root, args.original, args.destination, args.cache, args.author_repo, args.weights)))
