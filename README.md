# Science notes

Results found with AI research agents, collected in one place and sorted by field.
I am not a professional researcher in these fields. Each entry therefore says plainly
what is machine-checked, what is only argued on paper, and how novelty was checked.
Corrections are welcome via issues.

## Entries

| field | entry | claim | checked by |
|---|---|---|---|
| math | [triangle-free-grids](math/triangle-free-grids) | n × n grids contain sets without isosceles right triangles of size about n^1.3962 (previous exponent 1.3179) | Lean 4 proof, two independent certificate checkers |
| math | [unicyclic-distance-spectra](math/unicyclic-distance-spectra) | the only unicyclic graphs with exactly three distinct distance eigenvalues are C4 and C5 (an open problem from a 2024 paper) | paper proof; exhaustive computer check up to 12 vertices reported in the note |
| math | [covering-56-20-5](math/covering-56-20-5) | a covering design with 336 blocks, C(56, 20, 5) ≤ 336 (tables listed 693) | explicit construction; computer check of all five-subsets reported in the note |

## Layout

One folder per field (`math/`, later for example `biology/`, `physics/`), one subfolder
per result. Every result folder has its own README with the statement, how to reproduce
it, and how it was made.

## License

Code: MIT. Notes and data: CC BY 4.0. See `LICENSE`.
