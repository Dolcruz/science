# Unicyclic graphs with three distinct distance eigenvalues

**Claim.** A connected unicyclic graph has exactly three distinct distance eigenvalues if
and only if it is the 4-cycle C4 or the 5-cycle C5.

This answers Problem 1 of Hayat, Khan and Alenazi, *On Some Distance Spectral
Characteristics of Trees*, Axioms 13 (2024), 494: "Characterize all unicyclic graphs
having precisely three distinct distance eigenvalues."

## Contents

- `Unicyclic_distance_spectra.pdf`: the full proof (7 pages).
- `lean/`: the Lean 4 formalization (complete).

## Status

- **Formally proved in Lean 4 (Mathlib).** `lean/Unicyclic/Statement.lean` states the
  theorem; it was written and frozen before the proof was attempted. `Unicyclic.main`
  proves it, together with five sanity statements that pin down the definitions (for
  example, the distance spectrum of C4 is {4, 0, -2} and C6 has four distinct distance
  eigenvalues). `#print axioms` shows only `propext`, `Classical.choice` and `Quot.sound`:
  no `sorry`, no `native_decide`, no extra axioms. Reproduce with
  `cd lean && lake exe cache get && lake build`.
- The Lean proof follows its own route, not the note's: cycles are handled by their
  explicit spectra, long cycles with pendant leaves by a structural argument, and the
  triangle with pendant leaves by an algebraic identity
  (`lean/Unicyclic/TriangleAlgebra.lean`).
- The note reports an exact computer check of all 7872 unicyclic graphs with 3 to 12
  vertices, which finds only C4 and C5. The script for that check is not in this folder
  yet.
- Novelty was checked by literature search on 20 November 2026 (details in the note).
  Not peer reviewed, not submitted anywhere.

## How this was made

The proof and the note were written by AI agents (OpenAI Codex for the proof, Claude Code
for the readable rewrite and the re-check) at the request of Falk Pfisterer, who is not a
professional mathematician. Corrections are welcome via issues.
