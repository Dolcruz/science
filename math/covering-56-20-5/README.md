# A covering design with 336 blocks: 317 ≤ C(56, 20, 5) ≤ 336

**Claim.** There are 336 subsets of size 20 of a 56-point set such that every 5-subset
lies in at least one of them. The Covering Repository listed 693 blocks for this entry
(table read on 20 November 2026), and the frozen La Jolla archive lists 695.

The 56 points are the Hill cap in PG(5, 3). The blocks are the 308 hyperplane sections
with 20 points and 28 unions of pairs of the 56 sections with 11 points. The note also
proves that, once the 308 large sections are fixed, 28 further blocks are the minimum.
Consequences: C(56, 21, 5) ≤ 336 and C(55, 20, 5) ≤ 336.

## Contents

- `Covering_five_subsets.pdf`: construction and proofs (5 pages). It contains the full
  recipe for the 56 points, so the covering can be rebuilt from the note alone.

## Status

- The note reports that a program builds the 336 blocks and checks all 3,819,816
  five-subsets. That program and the block list are not in this folder yet.
- It is an upper bound only. Whether 336 is optimal is open (the lower bound is 317).
- Not peer reviewed and not yet submitted to the Covering Repository.

## How this was made

The construction and the note were produced by AI agents (OpenAI Codex for the
construction, Claude Code for the readable rewrite and the re-check) at the request of
Falk Pfisterer, who is not a professional mathematician. Corrections are welcome via
issues.
