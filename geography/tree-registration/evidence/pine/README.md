# Score the published small pine

From this directory, run the NumPy scorer on the [combined registration output](../../code/PAPER_INPUTS.md) for `small_pine_anim_42_0_2`. The authors’ original `small_pine_anim_42_0_2_out.npz` can be scored with the same command.

```sh
python score.py small_pine_registered.npz
```

The expected mean 3D endpoint error is **3.5146 cm** for the full pipeline and **3.6873 cm** for the original. Both use 43,161 points. Add `--point-errors errors.npy` to write each point’s error in metres in reference order. The scorer verifies every ordered source coordinate and the checksum of `reference.npz`.

The archive holds reference displacement vectors in metres and a separate zero-based row index for each source layout. We retained the corrected 5 cm metric points whose distance to a published source coordinate was below 1 µm. Full-pipeline indices use the regular source union. Original indices use the published nearest-coordinate correspondence, including its row choice for ties. This pair has no supplementary stationary source patches, so every retained point uses its predicted displacement. [Full-field verification](../pine-verification.json)

Derived from the S5 data by Hannah Weiser, Ronald Tabernig and Bernhard Höfle (2026). The reference vectors and row indices are distributed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). [Data and code](https://doi.org/10.11588/DATA/JQNDRP) · [Research article](https://doi.org/10.1093/forestry/cpag068)
