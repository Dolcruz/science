"""Fast scan-pair deformation from observed XYZ and predicted point matches, in metres."""

import numpy as np
from scipy.spatial import cKDTree


def _xyz(points, empty=False):
    value = np.asarray(points, dtype=np.float64)
    if value.ndim != 2 or value.shape[1] != 3 or (not empty and not len(value)) or not np.isfinite(value).all():
        raise ValueError("Expected finite XYZ coordinates")
    return value


def _centers(points, spacing):
    _, labels, counts = np.unique(np.floor(points / spacing).astype(np.int64),
                                  axis=0, return_inverse=True, return_counts=True)
    return np.column_stack([np.bincount(labels, weights=column) / counts for column in points.T])


def _neighbors(tree, query, k):
    return tree.query(query, k=list(range(1, min(k, tree.n) + 1)), workers=1)


def _interpolate(tree, values, query):
    out = np.empty((len(query), 3))
    for start in range(0, len(query), 16384):
        chunk = query[start:start + 16384]
        distance, index = _neighbors(tree, chunk, 4)
        # Keep coincident rows exact. Normalization by the closest distance
        # avoids overflow for almost coincident query/support pairs.
        weights = (np.maximum(distance[:, :1], 1.e-12) / np.maximum(distance, 1.e-12)) ** 2
        out[start:start + len(chunk)] = np.einsum("nk,nkd->nd", weights, values[index]) / weights.sum(1)[:, None]
    return out


def _landmark_prior(nodes, anchors):
    if anchors is None:
        return np.zeros_like(nodes), np.zeros(len(nodes))
    a, b = (_xyz(anchors[key], empty=True) for key in ("source", "target"))
    p = np.asarray(anchors["confidence"], dtype=float)
    if a.shape != b.shape or p.shape != (len(a),) or not np.isfinite(p).all() or np.any((p < 0) | (p > 1)):
        raise ValueError("Expected paired landmark arrays and matching probabilities")
    keep = p > .2
    if not np.any(keep):
        return np.zeros_like(nodes), np.zeros(len(nodes))
    a, displacement, confidence = a[keep], (b-a)[keep], p[keep]
    distance, index = _neighbors(cKDTree(a), nodes, 16)
    weights = confidence[index] / (.15 ** 2 + distance ** 2)
    # The local median keeps a single isolated high-confidence mismatch from
    # supplying the motion of a whole branch.
    proposals = displacement[index]
    center = np.median(proposals, axis=1)
    disagreement = np.linalg.norm(proposals - center[:, None], axis=2)
    robust_scale = .05 + np.median(disagreement, axis=1, keepdims=True)
    weights /= 1. + (disagreement / robust_scale) ** 2
    prior = np.einsum("nk,nkd->nd", weights, proposals) / weights.sum(1)[:, None]
    support = 1. / (1. + (distance[:, 0] / .4) ** 2)
    return prior, support


def register(source, target, anchors=None, initial=None):
    """Estimate source-to-target displacement on every source row. No training or GPU solver."""
    source, target = _xyz(source), _xyz(target)
    origin = source.min(axis=0)
    x, y = source - origin, target - origin
    if anchors is not None:
        anchors = {**anchors, **{key: _xyz(anchors[key], empty=True) - origin for key in ("source", "target")}}
    if initial is not None:
        raise ValueError("This estimator takes point matches as its initialization")
    previous = None
    for spacing in (.4, .15):
        nodes = _centers(x, spacing)
        dest = _centers(y, spacing / 2.)
        tree, target_tree = cKDTree(nodes), cKDTree(dest)
        prior, support = _landmark_prior(nodes, anchors)
        flow = (prior * support[:, None] if previous is None else _interpolate(*previous, nodes))
        d, neighbors = _neighbors(tree, nodes, 16)
        smooth = np.exp(-.5 * (d / spacing) ** 2)
        adjacency = smooth / smooth.sum(1)[:, None]
        for _ in range(4):
            warped = nodes + flow
            distance, ids = _neighbors(target_tree, warped, 4)
            weights = np.exp(-.5 * ((distance - distance[:, :1]) / (spacing / 2)) ** 2)
            expected = np.einsum("nk,nkd->nd", weights, dest[ids]) / weights.sum(1)[:, None]
            # Distant targets are often on another, visible branch. Their
            # influence falls off while nearby source nodes still share motion.
            w = 1. / (1. + (distance[:, 0] / spacing) ** 2) ** 2
            local = np.einsum("nk,nkd->nd", adjacency, flow[neighbors])
            weight_prior = .5 * support
            flow = ((expected - nodes) * w[:, None] + local + prior * weight_prior[:, None]) / (
                1. + w + weight_prior)[:, None]
        previous = tree, flow
    return _interpolate(*previous, x).astype(np.float32)
