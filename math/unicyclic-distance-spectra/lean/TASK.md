# Task: formalize the unicyclic theorem in Lean 4

Goal: prove `Unicyclic.MainStatement` (and the five sanity statements) from
`Unicyclic/Statement.lean`, following the paper proof in
`../Unicyclic_distance_spectra.pdf`.

## Done means

`lake build` succeeds in this folder with `Unicyclic/Statement.lean`, `Check.lean`,
`lakefile.toml`, `lean-toolchain` and `lake-manifest.json` byte-for-byte unchanged.
`Check.lean` then guarantees: every target is proved, no `sorry`, and only the axioms
`propext`, `Classical.choice`, `Quot.sound`.

## Rules

1. Do not edit the frozen files listed above. Write proofs in `Unicyclic/Proof.lean` and
   in further files under `Unicyclic/` that it imports.
2. No `sorry`, no `axiom`, no `native_decide`, no `unsafe`, no `implemented_by`, no
   `@[extern]`, no changes to the Mathlib pin.
3. If a target statement looks false, unprovable or different from what the note claims,
   stop and report this with the reason. Do not work around it by changing definitions.
4. Results missing from Mathlib (for example Perron-Frobenius for positive matrices,
   eigenvalue interlacing, Sylvester's law of inertia) must be proved here, or replaced by
   a different argument that is proved here. A different proof strategy than the note's
   is fine as long as the frozen statement is proved.
5. Work on a branch named `lean-unicyclic` and open a pull request. Do not push to `main`.
6. Report honestly. If the work is not finished, say exactly which lemmas are proved and
   which are open. A partial result with a clear list of open lemmas is useful; a build
   that only passes because a frozen file was changed is not.

## Setup

```bash
lake exe cache get
```

```bash
lake build
```

Right now the build fails in `Check.lean` because `Unicyclic/Proof.lean` contains
`sorry`. That is the intended starting state.

## Suggested order

1. `sanityPath`, `sanityCycle` (definitions only).
2. Distances in `cycleGraph n`, then the distance spectrum of cycles: `sanityC4`,
   `sanityC5`, `sanityC6` and the direction "C4 and C5 have three eigenvalues".
3. The structural part of the note (Sections 2 to 4) for the converse.
