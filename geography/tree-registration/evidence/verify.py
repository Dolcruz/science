"""Check the frozen pair table and print its equal-pair and equal-tree EPE."""

import csv
import hashlib
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean


TABLE = Path(__file__).resolve().with_name("paired_epe.csv")
TABLE_SHA256_LF = "deeb1c9c71b0cc34482ab9abc29bbae84bdfa16a11188e5d6ad282d03ca46413"
METHODS = ("mv", "direct", "windreg96", "full")
# (tree instances, directed pairs, scored source rows)
COVERAGE = {
    "published_s5": (20, 97, 22_145_252),
    "additional": (20, 200, 852_097),
    "initial_11": (11, 55, 3_153_708),
}


def check(condition, message):
    if not condition:
        raise ValueError(message)


def load():
    digest = hashlib.sha256(TABLE.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    check(digest == TABLE_SHA256_LF, "The paired table checksum has changed.")
    groups = defaultdict(list)
    pair_ids = set()
    with TABLE.open(encoding="ascii", newline="") as stream:
        for row in csv.DictReader(stream):
            dataset, group = row["dataset"], row["group"]
            pair_id, instance = row["pair_id"], row["instance"]
            source, target = row["source_epoch"], row["target_epoch"]
            check(dataset in COVERAGE, f"Unknown dataset for {pair_id}")
            check(source.isdecimal() and target.isdecimal() and source != target
                  and pair_id == f"{instance}_{source}_{target}", f"Invalid directed pair {pair_id}")
            check(pair_id not in pair_ids, f"Duplicate directed pair {pair_id}")
            pair_ids.add(pair_id)
            points = int(row["metric_points"])
            errors = tuple(float(row[f"{method}_epe_m"]) for method in METHODS)
            check(points > 0 and all(math.isfinite(x) and x >= 0 for x in errors),
                  f"Invalid coverage or EPE for {pair_id}")
            item = instance, points, errors
            groups[dataset].append(item)
            if dataset == "initial_11":
                check(group in ("familiar", "unseen"), f"Unknown preset group for {pair_id}")
                groups[group].append(item)
    for key, (trees, pairs, points) in COVERAGE.items():
        rows = groups[key]
        coverage = len({tree for tree, _, _ in rows}), len(rows), sum(n for _, n, _ in rows)
        check(coverage == (trees, pairs, points), f"Coverage mismatch for {key}: {coverage}")
    for key, trees in (("familiar", 9), ("unseen", 2)):
        counts = defaultdict(int)
        for tree, _, _ in groups[key]:
            counts[tree] += 1
        check(len(counts) == trees and set(counts.values()) == {5}, f"Coverage mismatch for {key}")
    wins = sum(errors[1] < errors[0] for _, _, errors in groups["published_s5"])
    check(wins == 97, f"The direct correction improved {wins}/97 published pairs.")
    return groups


def averages(vectors):
    return tuple(mean(column) for column in zip(*vectors))


def main():
    groups = load()
    print("EPE in metres. Each gain is relative to MV at the same weighting.")
    print(f"{'dataset':<13} {'weight':<6} {'trees':>5} {'pairs':>5}"
          f" {'mv':>9} {'direct':>9} {'windreg96':>9} {'full':>9}"
          f" {'direct gain':>12} {'windreg gain':>12} {'full gain':>10}")
    for name in (*COVERAGE, "familiar", "unseen"):
        rows = groups[name]
        by_tree = defaultdict(list)
        for tree, _, errors in rows:
            by_tree[tree].append(errors)
        for weighting, values in (
            ("pair", averages([errors for _, _, errors in rows])),
            ("tree", averages([averages(tree_rows) for tree_rows in by_tree.values()])),
        ):
            epe = " ".join(f"{value:9.6f}" for value in values)
            gains = [1 - value / values[0] for value in values[1:]]
            print(f"{name:<13} {weighting:<6} {len(by_tree):5} {len(rows):5} {epe}"
                  f" {gains[0]:12.2%} {gains[1]:12.2%} {gains[2]:10.2%}")
    print("The direct correction lowered EPE on all 97 published pairs.")


if __name__ == "__main__":
    main()
