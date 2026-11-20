"""Verify a digit alphabet for the Karolyi-Solymosi digit method.

Input file: first line "u v" (base beta = u + i v), then one digit "x y" per line,
in peeling order. Checks (A1) distinct residues, (A2) no carries, (A3) peeling order.
Integer arithmetic only.
"""
import sys, math


def load(path):
    rows = [l.split() for l in open(path) if l.strip() and not l.startswith('#')]
    u, v = map(int, rows[0])
    P = [tuple(map(int, r)) for r in rows[1:]]
    return (u, v), P


def residue(z, beta):
    (x, y), (u, v) = z, beta
    N = u * u + v * v
    return ((u * x + v * y) % N, (u * y - v * x) % N)


def verify(beta, P, verbose=True):
    u, v = beta
    N = u * u + v * v
    q = len(P)
    assert len(set(P)) == q
    res = {}
    for idx, p in enumerate(P):
        r = residue(p, beta)
        if r in res:
            return False, f"A1 fails: {P[res[r]]} ~ {p}"
        res[r] = idx
    pos = {p: k for k, p in enumerate(P)}
    nontriv = 0
    for kb, (bx, by) in enumerate(P):
        for kc, (cx, cy) in enumerate(P):
            # a = (1+i) b - i c
            ax = bx - by + cy
            ay = bx + by - cx
            r = residue((ax, ay), beta)
            if r in res:
                ka = res[r]
                if P[ka] != (ax, ay):
                    return False, f"A2 fails: b={P[kb]} c={P[kc]} a~{P[ka]} but needs {(ax, ay)}"
                if not (ka == kb == kc):
                    nontriv += 1
                    if not (ka < kb or kc < kb):
                        return False, f"A3 fails: a={P[ka]} b={P[kb]} c={P[kc]}"
    alpha = 2 * math.log(q) / math.log(N)
    return True, f"OK q={q} N={N} triangles={nontriv} alpha={alpha:.10f}"


if __name__ == '__main__':
    beta, P = load(sys.argv[1])
    ok, msg = verify(beta, P)
    print(msg)
    sys.exit(0 if ok else 1)
