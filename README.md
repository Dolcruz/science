# Science notes

[![checks](https://github.com/Dolcruz/science/actions/workflows/checks.yml/badge.svg)](https://github.com/Dolcruz/science/actions/workflows/checks.yml)

Results found with AI research agents, collected in one place and sorted by field.
I am not a professional researcher in these fields. Each entry therefore says plainly
what is machine-checked, what is only argued on paper, and how novelty was checked.
Corrections are welcome via issues.

## Entries

<!-- index:start -->
| field | entry | claim | checked by |
|---|---|---|---|
| mathematics | [Large grid sets without isosceles right triangles](math/triangle-free-grids) | F(n) >= c * n^alpha / sqrt(log n) with alpha = 2 log 313 / log 3757 = 1.3961707..., where F(n) is the largest subset of {0,...,n-1}^2 containing no isosceles right triangle in any orientation. | Lean 4 proof, certificate + checker |
| mathematics | [Unicyclic graphs with three distinct distance eigenvalues](math/unicyclic-distance-spectra) | A finite connected unicyclic graph has exactly three distinct distance eigenvalues if and only if it is isomorphic to the cycle C4 or the cycle C5. | Lean 4 proof |
| mathematics | [A (56, 20, 5) covering design with 336 blocks](math/covering-56-20-5) | C(56, 20, 5) <= 336: 336 subsets of size 20 of a 56-point set cover every 5-subset. | certificate + checker |
| geography | [July 2026 drainage of a western Greenland supraglacial lake](geography/glaciology/greenland-lake-2026-07) | A known Greenland basin lost 5.377 square kilometres of exposed water area between 20 and 23 July 2026, a 92.4% decline corroborated by Landsat and Sentinel-1 radar. | archival data analysis |
| geography | [Wind correction for tree laser scans](geography/tree-registration) | On 97 published simulated S5 scan pairs (Weiser, Tabernig and Hoefle 2026), mean 3D endpoint error of per-point displacement fell from 11.78 cm (MV-Tree-LNDP) to 8.98 cm (WindReg96 with local correction), a 23.77% reduction; 22.37% on 11 newly simulated trees. | reproducible evaluation |
| physics | [An apparently uncataloged earthquake in the Brawley swarm](physics/seismology/brawley-2026-05-10) | Ten stations support a small local earthquake near Brawley at about 03:30:02 UTC on 10 May 2026, with a relative magnitude estimate of 1.4 and no matching event in the six catalog products checked. | archival data analysis |
| physics | [Locating the 2.709-day eclipse near TIC 349414709](physics/astronomy/tic-349414709) | Forty TESS eclipse timings and Bochum photometry locate a published signal near TIC 349414709, about 15 arcseconds from the originally listed target TIC 349414705. | archival data analysis |
| physics | [What eclipses TIC 153838604?](physics/astronomy/tic-153838604) | Four TESS eclipses (sectors 5, 32, 97, 98) follow a 56.0793594-day period over 2018 to 2025 (maximum residual 3.2 minutes), resolving the period alias of the duotransit candidate CTOI 153838604.01. | archival data analysis |
<!-- index:end -->

The table is generated from [index.json](index.json), which also lists the exact
verification command, the Lean theorem name, key numbers and limits of every entry.
Agents: see [llms.txt](llms.txt) and [AGENTS.md](AGENTS.md).

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
