"""Independent brute-force check of (A1)-(A3): all q^3 ordered triples (a,b,c),
test whether beta divides a + i c - (1+i) b, and if so require it to be 0 and,
for non-constant solutions, an endpoint earlier than the centre. numpy int64."""
import sys, math
import numpy as np

rows = [l.split() for l in open(sys.argv[1]) if l.strip()]
u, v = map(int, rows[0]); N = u * u + v * v
P = np.array([[int(x), int(y)] for x, y in rows[1:]], dtype=np.int64)
q = len(P)
X, Y = P[:, 0], P[:, 1]
# z * conj(beta) = (u x + v y) + i (u y - v x); beta | z  iff both parts = 0 mod N
ok = True
# A1
codes = set()
for x, y in P.tolist():
    c = ((u * x + v * y) % N, (u * y - v * x) % N)
    if c in codes:
        ok = False; print("A1 fails")
    codes.add(c)
sols = 0; nonconst = 0
idx = np.arange(q)
for kb in range(q):
    bx, by = X[kb], Y[kb]
    # z = a + i c - (1+i) b, over all a (axis 0), c (axis 1)
    zx = X[:, None] - Y[None, :] - (bx - by)
    zy = Y[:, None] + X[None, :] - (bx + by)
    div = ((u * zx + v * zy) % N == 0) & ((u * zy - v * zx) % N == 0)
    if not div.any():
        continue
    zero = (zx == 0) & (zy == 0)
    if (div & ~zero).any():
        ok = False; print("A2 fails at centre", P[kb])
    ka, kc = np.nonzero(div)
    for a, c in zip(ka.tolist(), kc.tolist()):
        sols += 1
        if a == kb == c:
            continue
        nonconst += 1
        if not (a < kb or c < kb):
            ok = False; print("A3 fails", P[a], P[kb], P[c])
print(f"{'OK' if ok else 'FAIL'} q={q} N={N} solutions={sols} nonconstant={nonconst} "
      f"triples_checked={q**3} alpha={2*math.log(q)/math.log(N):.10f}")
sys.exit(0 if ok else 1)
