"""Regenerate the digit array in IRT/Digits.lean from a certificate file.
usage: python3 gen_digits.py ../certificates/alphabet_61+6i_313.txt
Prints the array literal; the rest of Digits.lean is written by hand."""
import sys
rows = [l.split() for l in open(sys.argv[1]) if l.strip()]
assert rows[0] == ['61', '6']
P = [(int(a), int(b)) for a, b in rows[1:]]
print('#[\n  ' + ',\n  '.join(', '.join(f'({x}, {y})' for x, y in P[k:k + 8])
                              for k in range(0, len(P), 8)) + ']')
