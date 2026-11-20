"""Rebuild the 336-block (56, 20, 5) covering from the Hill cap and check it.

Recipe (from the note): read each of the eight strings as the coefficients of a
polynomial of degree at most 6 over F_3, constant term first. For i = 0..5, multiply
all eight polynomials by x^i and reduce modulo x^7 - 2. The eight coefficient lists
(seven numbers each) of step i, written one after another, form row i of a 6 x 56
matrix G. The 56 points are the columns of G.

Blocks: the 308 hyperplane sections with 20 points, and the 56 sections with 11 points
split into 28 pairs (consecutive in the order found); each pair's union has 20 points.

usage: python3 build_and_check.py [--write ../data/blocks_56_20_5.txt]
Standard library only. Points are numbered 1..56 in column order.
"""
import itertools, sys

STRINGS = ["1000002", "2110100", "1102021", "1110010", "1201021", "2111112", "2001200", "2012211"]
P = 3

def mul_x(c):  # multiply by x modulo x^7 - 2 over F_3 (x^7 = 2)
    return [(2 * c[6]) % P] + c[:6]

def build_G():
    polys = [[int(ch) for ch in s] for s in STRINGS]
    rows = []
    for i in range(6):
        row = []
        for p in polys:
            q = p
            for _ in range(i):
                q = mul_x(q)
            row += q
        rows.append(row)
    return rows

def main():
    G = build_G()
    n = len(G[0]); assert n == 56
    cols = [tuple(G[r][j] for r in range(6)) for j in range(n)]
    # normals up to scalar: first nonzero coordinate equal to 1
    normals = [a for a in itertools.product(range(P), repeat=6)
               if any(a) and a[next(k for k in range(6) if a[k])] == 1]
    assert len(normals) == 364
    sections = []
    for a in normals:
        sec = frozenset(j for j in range(n) if sum(x * y for x, y in zip(a, cols[j])) % P == 0)
        sections.append(sec)
    assert len(set(sections)) == 364, "sections not distinct"
    sizes = sorted({len(s) for s in sections})
    large = [s for s in sections if len(s) == 20]
    short = [s for s in sections if len(s) == 11]
    assert sizes == [11, 20] and len(large) == 308 and len(short) == 56, sizes
    # cap: no three collinear points, i.e. no three columns pairwise projectively distinct
    # and linearly dependent. Check: no column is a multiple of another, and no
    # a*u + b*v (a, b nonzero) equals another column up to scalar.
    projective = {}
    for j, c in enumerate(cols):
        k = next(t for t in range(6) if c[t]); inv = 1 if c[k] == 1 else 2
        projective[tuple((inv * x) % P for x in c)] = j
    assert len(projective) == 56, "two columns are multiples of each other"
    for u, v in itertools.combinations(range(n), 2):
        for b in (1, 2):
            w = tuple((cols[u][t] + b * cols[v][t]) % P for t in range(6))
            k = next(t for t in range(6) if w[t]); inv = 1 if w[k] == 1 else 2
            w = tuple((inv * x) % P for x in w)
            assert projective.get(w) is None, "three collinear points"
    for s, t in itertools.combinations(short, 2):
        assert len(s & t) == 2
    blocks = [sorted(s) for s in large]
    for k in range(0, 56, 2):
        u = short[k] | short[k + 1]
        assert len(u) == 20
        blocks.append(sorted(u))
    assert len(blocks) == 336 and all(len(b) == 20 for b in blocks)
    # coverage: mark every 5-subset of every block
    def rank(q):  # combinatorial number system index of a sorted 5-subset of range(56)
        from math import comb
        return sum(comb(x, i + 1) for i, x in enumerate(q))
    covered = bytearray(3819816)
    for b in blocks:
        for q in itertools.combinations(b, 5):
            covered[rank(q)] = 1
    missing = covered.count(0)
    print(f"cap ok, sections 308 x 20 + 56 x 11, short sections meet in 2 points")
    print(f"blocks: {len(blocks)}, each of size 20; uncovered 5-subsets: {missing} of 3819816")
    assert missing == 0
    if "--write" in sys.argv:
        path = sys.argv[sys.argv.index("--write") + 1]
        with open(path, "w") as f:
            f.write("# (56, 20, 5) covering with 336 blocks; points 1..56; one block per line\n")
            for b in blocks:
                f.write(" ".join(str(x + 1) for x in b) + "\n")
        print("wrote", path)
    print("OK")

if __name__ == "__main__":
    main()
