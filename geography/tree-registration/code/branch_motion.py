"""Smooth a dense predicted tree motion field with robust local affine fits."""

import numpy as np
from scipy.spatial import cKDTree


_BLOCK = 16384
_VOXEL_RECORD = np.dtype([("cell", np.int64, 3), ("distance", np.float64), ("row", np.intp)])


def _xyz_array(value, name):
    points = np.asarray(value)
    if points.ndim != 2 or points.shape[1] != 3 or not len(points):
        raise ValueError(f"{name} must be a nonempty (N, 3) array")
    return points


def _voxel_winners(records):
    cells = records["cell"]
    order = np.lexsort((records["row"], records["distance"], cells[:, 2], cells[:, 1], cells[:, 0]))
    ordered = cells[order]
    first = np.r_[True, np.any(ordered[1:] != ordered[:-1], axis=1)]
    return records[order[first]]


def voxel_representatives(points, size_m):
    """Choose the nearest point to every voxel centre; ties use the earliest input row."""
    points = _xyz_array(points, "source")
    if not np.isfinite(size_m) or size_m <= 0:
        raise ValueError("Voxel size must be positive and finite")
    levels = []
    for start in range(0, len(points), _BLOCK):
        part = np.asarray(points[start:start + _BLOCK], dtype=np.float64)
        if not np.isfinite(part).all():
            raise ValueError("Source contains non-finite coordinates")
        local = np.empty(len(part), dtype=_VOXEL_RECORD)
        cells = np.floor(part / size_m).astype(np.int64)
        local["cell"] = cells
        local["distance"] = np.sum((part - (cells + .5) * size_m) ** 2, axis=1)
        local["row"] = np.arange(start, start + len(part))
        winners = _voxel_winners(local)
        # A global minimum in a cell is also a local minimum in its input block.
        # Merge equally sized groups of blocks to avoid rescanning early winners
        # on every new block. Original distances and global row indices survive.
        level = 0
        while level < len(levels) and levels[level] is not None:
            winners = _voxel_winners(np.concatenate((levels[level], winners)))
            levels[level] = None
            level += 1
        if level == len(levels):
            levels.append(winners)
        else:
            levels[level] = winners
    runs = (group for group in levels if group is not None)
    winners = next(runs)
    for group in runs:
        winners = _voxel_winners(np.concatenate((winners, group)))
    return np.sort(winners["row"])


def _spatial_weights(distance, spacing):
    # Removing the common exponent preserves weights even for isolated points.
    relative_square = (distance - distance[:, :1]) * (distance + distance[:, :1])
    return np.exp(-relative_square / (2 * spacing ** 2))


def _affine(offset, motion, weight, ridge):
    weight = weight / weight.sum(axis=1, keepdims=True)
    center = np.einsum("nk,nki->ni", weight, offset)
    mean = np.einsum("nk,nki->ni", weight, motion)
    x, y = offset - center[:, None], motion - mean[:, None]
    covariance = np.einsum("nki,nk,nkj->nij", x, weight, x)
    cross = np.einsum("nki,nk,nkj->nij", x, weight, y)
    slope = np.linalg.solve(covariance + ridge, cross)
    intercept = mean - np.einsum("ni,nij->nj", center, slope)
    return intercept, slope


def register(source, target=None, anchors=None, initial=None, *, spacing=.4):
    """Return affine-smoothed flow in source row order. Positions and spacing are in metres."""
    if initial is None:
        raise ValueError("Expected a full initial motion field")
    source, initial = _xyz_array(source, "source"), _xyz_array(initial, "initial flow")
    if source.shape != initial.shape:
        raise ValueError("Initial flow must match the source shape")
    if not np.isfinite(spacing) or spacing <= 0.:
        raise ValueError("Spacing must be finite and positive")
    rows = voxel_representatives(source, spacing / 2.)
    for start in range(0, len(initial), _BLOCK):
        if not np.isfinite(np.asarray(initial[start:start + _BLOCK], dtype=np.float64)).all():
            raise ValueError("Initial flow contains non-finite displacements")
    nodes = np.asarray(source[rows], dtype=np.float64)
    flow = np.asarray(initial[rows], dtype=np.float64)
    tree = cKDTree(nodes)
    fit_ranks = list(range(1, min(32, len(nodes)) + 1))
    blend_ranks = list(range(1, min(4, len(nodes)) + 1))
    slopes = np.empty((len(nodes), 3, 3))
    intercepts = np.empty_like(nodes)
    ridge = .01 * spacing ** 2 * np.eye(3)
    for start in range(0, len(nodes), 1024):
        block = slice(start, start + 1024)
        distance, index = tree.query(nodes[block], k=fit_ranks, workers=1)
        offset = nodes[index] - nodes[block, None]
        motion = flow[index]
        spatial = _spatial_weights(distance, spacing)
        intercept, slope = _affine(offset, motion, spatial, ridge)
        for _ in range(2):
            predicted = intercept[:, None] + np.einsum("nki,nij->nkj", offset, slope)
            error = np.linalg.norm(motion - predicted, axis=2)
            mad = np.median(np.abs(error - np.median(error, axis=1, keepdims=True)), axis=1, keepdims=True)
            cutoff = 1.345 * np.maximum(.025, 1.4826 * mad)
            robust = cutoff / np.maximum(error, cutoff)
            intercept, slope = _affine(offset, motion, spatial * robust, ridge)
        slopes[block] = slope
        intercepts[block] = intercept
    result = np.empty(source.shape, dtype=np.float32)
    for start in range(0, len(source), _BLOCK):
        block = slice(start, start + _BLOCK)
        points = np.asarray(source[block], dtype=np.float64)
        distance, index = tree.query(points, k=blend_ranks, workers=1)
        weight = _spatial_weights(distance, spacing)
        weight /= weight.sum(axis=1, keepdims=True)
        offset = points[:, None] - nodes[index]
        fitted = intercepts[index] + np.einsum("nki,nkij->nkj", offset, slopes[index])
        result[block] = np.einsum("nk,nki->ni", weight, fitted)
        if not np.isfinite(result[block]).all():
            raise FloatingPointError("Local affine fits produced nonfinite displacement")
    return result
