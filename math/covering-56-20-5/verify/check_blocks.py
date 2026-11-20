"""Check a block file alone: every 5-subset of {1..56} lies in some block.

usage: python3 check_blocks.py ../data/blocks_56_20_5.txt
Standard library only. Independent of how the blocks were built.
"""
import itertools, sys
from math import comb

V, K, T = 56, 20, 5
blocks = [list(map(int, l.split())) for l in open(sys.argv[1]) if l.strip() and not l.startswith("#")]
assert all(len(b) == K and len(set(b)) == K and all(1 <= x <= V for x in b) for b in blocks)
covered = bytearray(comb(V, T))
for b in blocks:
    for q in itertools.combinations(sorted(x - 1 for x in b), T):
        covered[sum(comb(x, i + 1) for i, x in enumerate(q))] = 1
missing = covered.count(0)
print(f"{len(blocks)} blocks of size {K} on {V} points; uncovered {T}-subsets: {missing} of {comb(V, T)}")
sys.exit(0 if missing == 0 else 1)
