# Rules for new entries

This repository collects research results produced with AI agents. Producing a result is
cheap; checking it is not. These rules exist so that every entry can be trusted to the
degree it says, no more. They apply to every agent and every person adding an entry.

An entry is merged into `main` only when all six gates below are passed and recorded in
the entry's README.

## Gate 1: Evidence that others can rerun

Pick the strongest kind that fits the result.

| Kind of result | Required evidence |
|---|---|
| Theorem | A Lean 4 proof, or a finite certificate with a checker. A paper proof alone is allowed only if the README says so in its first lines. |
| Construction (design, code, alphabet, bound) | The object itself as a file, plus a checker that verifies the claimed property from that file alone. |
| Empirical result | Code that recomputes every reported number from the data, and a script that checks the reported table against the stored measurements. |
| Observation or data analysis | Raw input identifiers (archive IDs, DOIs, hashes), the analysis code, and the exact commands. |

For Lean proofs:

- The target statement is written and frozen **before** the proof is attempted, in its own
  file, together with sanity statements that would fail if a definition were wrong.
- A check file enforces that the frozen statement is proved and prints the axioms.
- Allowed axioms are `propext`, `Classical.choice` and `Quot.sound`. Anything else
  (`native_decide`, `sorry`, new `axiom`s) must be named in the README's first lines.

## Gate 2: Independent review

A reviewer that did **not** produce the result checks it. The reviewer's task is to find
errors, not to confirm.

- Rebuild or rerun everything from a fresh checkout of the exact commit.
- Confirm that frozen statement files are byte-identical to their frozen version.
- Scan for `sorry`, `axiom`, `native_decide`, `unsafe`, `implemented_by`, `@[extern]` and
  environment manipulation, and read any custom tactic or elaborator.
- For empirical work, look specifically for data leakage, tuning on the test set,
  cherry-picked subsets, and metrics that improve while another relevant metric worsens.
- Recompute at least one headline number from the raw archive data with your own code,
  including unit and scaling conventions (for example, whether a reflectance offset has
  already been applied by the data provider).
- Test a claimed signal against the same statistic at control positions or times.
- Record in the README: who reviewed (agent and model, or person), which commit, what was
  rerun, and what was found.

## Gate 3: Novelty search

- Search the literature, preprint servers and the relevant record tables or databases.
- Write down in the README what was searched, on which date, and what was found.
- Say "no earlier result found" only if that is what the search showed. If the search
  could not reach a source (paywall, blocked site), say so.

## Gate 4: Limits stated first

The README opens with the claim and, directly below it, what the claim does **not** show.
Examples: "retrospective on a test set that was known during development", "simulation
only", "conditional on an unpublished certificate", "upper bound only, optimum open".

## Gate 5: Empirical work is pre-registered where possible

- Fix the evaluation protocol, the cohort and the metrics before scoring new data, and
  store a hash of the protocol in the repository.
- Report the pre-registered result even if it is worse than the retrospective one.
- If a result was picked from a search (a candidate, an event, a feature), say how many
  comparable candidates the same search produced and how this one compares. A single
  extreme from a large search is not a finding by itself; often the list is the result.
- Do not change a pre-registered cohort after scoring has started. A new question gets a
  new protocol.

## Gate 6: Credit, licences and disclosure

- Name the authors whose methods, data or problems the entry builds on, with links.
- Keep third-party licences and notices; respect dataset terms.
- State plainly which parts were produced by AI agents and which by people.
- No private data: no personal addresses, phone numbers, credentials or internal paths.

## Workflow

1. Work on a branch named after the entry, never directly on `main`.
2. Put the entry under `<field>/<entry-name>/` (subfields allowed, for example
   `physics/astronomy/`). Do not modify other entries.
3. Open a pull request that lists how each gate was passed.
4. After independent review, merge and add one row to the table in the root `README.md`.

## Before contacting anyone

When an entry improves on or answers someone's published work, the authors are usually
the right people to tell, and telling them early matters for priority. Send one short,
honest message per entry, only after all gates are passed, with a link to the entry and
a plain note on how it was produced. Prefer fewer, well-checked entries over many.
