# Notes for AI agents

This file is for automated agents that read, reuse or extend this repository. Humans
can read it too.

## Using a result

1. Start from [index.json](index.json). Each entry gives the claim in plain text, the
   key numbers, the evidence level (`status`), the exact verification command, the Lean
   theorem name where there is one, the limits, and the work it builds on.
2. Read the entry's `limitations` before using its claim as a step in your own work.
   They are part of the claim.
3. Trust levels, strongest first: `lean-proof` (checked by the Lean 4 kernel; the axioms
   are listed), `certificate` (an explicit object and a checker that verifies it),
   `reproducible-empirical`, `archival-analysis`, `paper-proof`.
4. To verify, run the `command` field from the repository root. Python checkers use only
   the standard library unless the entry says otherwise. Lean projects pin their Lean
   version and Mathlib commit; `lake exe cache get && lake build` reproduces the proof.
5. Lean statements of the form `Name.main` are stated in a separate frozen statement file
   where the entry says so. Check that file to see exactly what is proved.

## Citing

Cite the entry folder and commit, for example
`Dolcruz/science, math/covering-56-20-5, commit <hash>`. See [CITATION.cff](CITATION.cff).
Also cite the original work listed in the entry's `builds_on` field.

## Reporting a problem

Open an issue with the entry id, the commit, the command you ran and what failed. Errors
found by agents are welcome and will be fixed or stated in the entry.

## Adding an entry

Follow [CONTRIBUTING.md](CONTRIBUTING.md). In short: work on a branch, one folder per
entry, rerunnable evidence, an independent review, a dated novelty search, limits first.
Then add the entry to `index.json` and run `python3 tools/build_index.py`, which updates
the table in `README.md` and `llms.txt`. `python3 tools/build_index.py --check` must pass.
