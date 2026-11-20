# Large grid sets without isosceles right triangles: exponent 1.3962

Let F(n) be the largest number of points of the n × n integer grid such that no three of
them form an isosceles right triangle (in any orientation).

**Result.** F(n) ≥ c · n^α / √(log n) with α = 2·log 313 / log 3757 = 1.39617…

The previous best exponent known to us is 1.317865… (Károlyi and Solymosi,
[arXiv:2607.22828](https://arxiv.org/abs/2607.22828), July 2026). The method is theirs: a
Salem-Spencer-type digit construction in a Gaussian-integer base. What is new here is a
better digit alphabet (313 digits in base 61 + 6i), a simpler level argument, a lemma that
characterises their "peeling order" condition, and a Lean 4 formalization.

## What is machine-checked

`lean/` proves, in Lean 4 with Mathlib (`IRT.main` in `lean/IRT/Main.lean`):

> For all natural numbers m, n with 3757^m ≤ n², the grid {0, …, n−1}² contains a set
> without isosceles right triangles that has at least ⌊313^m / (m · 2^312 + 1)⌋ points.

Choosing m = ⌊2 log n / log 3757⌋ gives F(n) ≥ c · n^α / log n. The sharper factor
√(log n) is proved on paper in the note (Chebyshev instead of pigeonhole) and is not
formalized.

`#print axioms IRT.main` reports `propext`, `Classical.choice`, `Quot.sound` and one axiom
created by `native_decide`: the finite check of all 313³ = 30,664,297 digit triples is run
as compiled code, not inside the Lean kernel.

## Contents

| folder | what |
|---|---|
| `note/` | the write-up (`IRT_free_grids.pdf`) and its source |
| `certificates/` | digit alphabets: first line `u v` (base u + iv), then one digit `x y` per line, in peeling order |
| `verify/` | two independent Python checkers for a certificate file (standard library; `verify2.py` needs numpy) |
| `lean/` | the Lean 4 formalization |
| `search/` | the local search that found the alphabets (C) |

## Reproduce

```bash
python3 verify/verify.py certificates/alphabet_61+6i_313.txt
```

```bash
python3 verify/verify2.py certificates/alphabet_61+6i_313.txt
```

```bash
cd lean && lake exe cache get && lake build
```

```bash
gcc -O2 -o search/search search/search.c -lm && ./search/search 61 6 26 600 1
```

The search arguments are: base u, base v, candidate radius, seconds, random seed, and
optionally a certificate file to start from and a starting temperature.

## How this was made

The search program, the proofs, the Lean formalization and the note were written by AI
coding agents (Anthropic's Claude Code; the earlier 253-digit alphabet in
`certificates/alphabet_61+6i_253_earlier.txt` came from OpenAI's Codex) at the request of
Falk Pfisterer, who is not a professional mathematician. The correctness of the
machine-checked statement does not depend on trusting any of them: it rests on the Lean
proof and on the certificate, which anyone can re-run. Whether the result is new was
checked only by literature search (20 November 2026); corrections are welcome via issues.

## License

Code: MIT. Note and certificates: CC BY 4.0.
