# Science notes

Results found with AI research agents, collected in one place and sorted by field.
I am not a professional researcher in these fields. Each entry therefore says plainly
what is machine-checked, what is only argued on paper, and how novelty was checked.
Corrections are welcome via issues.

## Entries

| field | entry | claim | checked by |
|---|---|---|---|
| math | [triangle-free-grids](math/triangle-free-grids) | n × n grids contain sets without isosceles right triangles of size about n^1.3962 (previous exponent 1.3179) | Lean 4 proof, two independent certificate checkers |
| math | [unicyclic-distance-spectra](math/unicyclic-distance-spectra) | the only unicyclic graphs with exactly three distinct distance eigenvalues are C4 and C5 (an open problem from a 2024 paper) | Lean 4 proof (no extra axioms) |
| math | [covering-56-20-5](math/covering-56-20-5) | a covering design with 336 blocks, C(56, 20, 5) ≤ 336 (tables listed 693) | explicit construction; computer check of all five-subsets reported in the note |
| geography | [Wind correction for tree laser scans](geography/tree-registration) | mean 3D motion error fell from 11.78 to 8.98 cm on 97 published simulated scan pairs | paired scores, runnable example and full-field reproduction on one published pair |
| physics / astronomy | [What eclipses TIC 153838604?](physics/astronomy/tic-153838604) | a giant planet and a faint red dwarf both fit four TESS eclipses recurring every 56.07936 days | TESS timing and pixel analysis, independent survey photometry, Gaia and radial-velocity archive checks |

## Quality rules

Every entry has to pass the gates in [CONTRIBUTING.md](CONTRIBUTING.md): evidence that
others can rerun, an independent review, a documented novelty search, limits stated up
front, pre-registration for empirical work, and clear credit and AI disclosure.

## Layout

Results are grouped by field (`math/`, `geography/`, `physics/`) and, where useful, by subfield.
Each result has a README describing the claim, its provenance and how to reproduce it.
New research reports are typeset with LaTeX or an equivalent system and published as reader-ready PDFs.

## License

Code: MIT. Notes and data: CC BY 4.0. See `LICENSE`. Third-party components retain the licenses listed in their entries.
