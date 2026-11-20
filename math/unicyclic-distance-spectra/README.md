# Unicyclic graphs with three distinct distance eigenvalues

**Claim.** A connected unicyclic graph has exactly three distinct distance eigenvalues if
and only if it is the 4-cycle C4 or the 5-cycle C5.

This answers Problem 1 of Hayat, Khan and Alenazi, *On Some Distance Spectral
Characteristics of Trees*, Axioms 13 (2024), 494: "Characterize all unicyclic graphs
having precisely three distinct distance eigenvalues."

## Contents

- `Unicyclic_distance_spectra.pdf`: the full proof (7 pages).
- `lean/`: target statement for the Lean 4 formalization (work in progress).

## Status

- The proof is a paper proof. It is not formalized yet. `lean/` contains the frozen target
  statement for a Lean 4 formalization (`lean/Unicyclic/Statement.lean`) and the rules for
  it (`lean/TASK.md`); the proofs there are still open.
- The note reports an exact computer check of all 7872 unicyclic graphs with 3 to 12
  vertices, which finds only C4 and C5. The script for that check is not in this folder
  yet.
- Novelty was checked by literature search on 20 November 2026 (details in the note).
  Not peer reviewed, not submitted anywhere.

## How this was made

The proof and the note were written by AI agents (OpenAI Codex for the proof, Claude Code
for the readable rewrite and the re-check) at the request of Falk Pfisterer, who is not a
professional mathematician. Corrections are welcome via issues.
